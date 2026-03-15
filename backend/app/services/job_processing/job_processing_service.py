import json
import logging
import asyncio
from functools import partial
from pathlib import Path
from fastapi import HTTPException
from app.services.s3_service import S3Service
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from app.schemas.job_payload import PrepareJobPayload
from app.schemas.matching_preferences import MatchingPreferences
from datetime import datetime, timezone
from app.llm_models.llm_factory import get_llm
from app.services.job_processing.jd_parser import JDParser
from app.services.job_processing.resume_parser import ResumeParser
from app.services.job_processing.matcher import MatchingOrchestrator
from app.utils.set_flag import get_job_flag, set_job_flag
from app.utils.load_json import load_json
from app.events.event_bus import event_bus
from app.events.events_types import (
    JOB_STARTED, JOB_FAILED, JOB_COMPLETED,
    JD_PARSING_STARTED, JD_PARSING_COMPLETED,
    RESUMES_PARSING_STARTED, RESUMES_PARSING_COMPLETED,
    RESUME_PARSING_STARTED, RESUME_PARSING_COMPLETED,
    RESUMES_MATCHING_STARTED, RESUMES_MATCHING_COMPLETED,
    RESUME_MATCHING_STARTED, RESUME_MATCHING_COMPLETED,
    SUMMARY_UPDATED, RESUMES_RANKING_COMPLETED, RESUMES_RANKING_STARTED,
    TIMING_EVENT
)
from app.events.event_models import (
    JobStartedEvent, JobFailedEvent, JobCompletedEvent,
    JdParsingStartedEvent, JdParsingCompletedEvent,
    ResumesParsingStartedEvent, ResumesParsingCompletedEvent,
    ResumeParsingStartedEvent, ResumeParsingCompletedEvent,
    ResumesMatchingStartedEvent, ResumesMatchingCompletedEvent,
    ResumeMatchingStartedEvent, ResumeMatchingCompletedEvent,
    SummaryUpdatedEvent, ResumesRankingStartedEvent, ResumesRankingCompletedEvent,
    TimingEvent
)

import yaml

logger = logging.getLogger(__name__)
OUTPUT_BASE_DIR = Path("output")
OUTPUT_BASE_DIR.mkdir(exist_ok=True)

BASE_DIR    = Path(__file__).resolve().parents[3]
CONFIG_PATH = BASE_DIR / "app" / "config" / "llm_config.yml"
with open(CONFIG_PATH) as f:
    config = yaml.safe_load(f)
llm_instance = get_llm(config["llm_model"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobProcessingService:
    """
    Orchestrator — calls pure parsers/matchers, then emits events.
    Blocking calls are offloaded to a thread pool via run_in_executor
    so FastAPI's event loop stays free for other requests.
    The public entry point (submit_job) returns immediately;
    all heavy work runs in the background via _process_job.
    """

    def __init__(self):
        s3      = S3Service()
        jobs    = JobService()
        resumes = ResumeService(llm_instance)

        self.jd_parser     = JDParser(jobs, s3)
        self.resume_parser = ResumeParser(resumes, s3)
        self.matcher       = MatchingOrchestrator()

    # ─────────────────────────────────────────────────────────────────────────
    # PUBLIC — called by the router. Returns instantly; processing is async.
    # ─────────────────────────────────────────────────────────────────────────
    async def submit_job(
        self,
        drive_id: str,
        payload: PrepareJobPayload,
        base_weight: float = 0.90,
        additional_weight: float = 0.10,
        preferences: MatchingPreferences = None,
    ) -> dict:
        """
        Validates the request, marks the job as 'in progress' (flag=0),
        fires off _process_job as a background task, and returns immediately.
        The client should poll GET /result/{drive_id} to check completion.
        """
        jd_id = payload.jd.jdId

        # Mark job as started BEFORE launching background work so that
        # any immediate poll returns 409 (Ongoing) rather than 404 (Not found).
        job_folder     = OUTPUT_BASE_DIR / drive_id
        resumes_folder = job_folder / "resumes"
        job_folder.mkdir(parents=True, exist_ok=True)
        resumes_folder.mkdir(exist_ok=True)
        set_job_flag(drive_id, 0)

        # Fire and forget — does NOT await, so this returns immediately.
        asyncio.create_task(
            self._process_job(
                drive_id=drive_id,
                payload=payload,
                job_folder=job_folder,
                resumes_folder=resumes_folder,
                base_weight=base_weight,
                additional_weight=additional_weight,
                preferences=preferences,
            )
        )

        return {
            "driveId": drive_id,
            "jdId":    jd_id,
            "status":  "queued",
            "message": "Job accepted. Poll /result/{drive_id} for progress.",
        }

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE — the actual heavy lifting, runs in the background
    # ─────────────────────────────────────────────────────────────────────────
    async def _process_job(
        self,
        drive_id: str,
        payload: PrepareJobPayload,
        job_folder: Path,
        resumes_folder: Path,
        base_weight: float,
        additional_weight: float,
        preferences: MatchingPreferences,
    ) -> None:

        loop          = asyncio.get_event_loop()
        jd_id         = payload.jd.jdId
        total_resumes = len(payload.resumes)
        summary_path  = str(job_folder / "summary.json")

        summary = {
            "job_id":   drive_id,
            "jd_id":    jd_id,
            "jd_parsing": 0,
            "resume_parsing":     {"completed": 0, "total": total_resumes},
            "jd_resume_matching": {"completed": 0, "total": total_resumes},
        }

        # ── initial summary + job started ────────────────────────────────────
        await event_bus.publish(SummaryUpdatedEvent(
            type=SUMMARY_UPDATED, summary_path=summary_path, summary=summary,
        ))
        await event_bus.publish(JobStartedEvent(
            type=JOB_STARTED, drive_id=drive_id,
            jd_id=jd_id, total_resumes=total_resumes,
        ))

        try:
            # =================================================================
            # STEP 1 — JD Parsing
            # run_in_executor offloads the blocking call to a thread,
            # keeping the event loop free for other requests.
            # =================================================================
            await event_bus.publish(JdParsingStartedEvent(
                type=JD_PARSING_STARTED, drive_id=drive_id, jd_id=jd_id,
            ))
            jd_start = _now()

            jd_result = await loop.run_in_executor(
                None,  # default ThreadPoolExecutor
                partial(
                    self.jd_parser.parse,
                    drive_id, jd_id, payload.jd.fileUrl, job_folder,
                )
            )

            jd_end = _now()

            if jd_result["status"] == "failed":
                await event_bus.publish(JobFailedEvent(
                    type=JOB_FAILED, drive_id=drive_id,
                    jd_id=jd_id, error=jd_result["error"],
                ))
                return  # exit background task; flag stays 0 (ongoing)
                        # caller can check summary or add a "failed" flag value

            summary["jd_parsing"] = 1
            await event_bus.publish(JdParsingCompletedEvent(
                type=JD_PARSING_COMPLETED,
                drive_id=drive_id, jd_id=jd_id,
                job_dict=jd_result["job_dict"],
                job_path=jd_result["job_path"],
            ))
            await event_bus.publish(SummaryUpdatedEvent(
                type=SUMMARY_UPDATED, summary_path=summary_path, summary=summary,
            ))
            await event_bus.publish(TimingEvent(
                type=TIMING_EVENT, drive_id=drive_id,
                label="JD Parsing",
                started_at=jd_start, completed_at=jd_end,
            ))

            # =================================================================
            # STEP 2 — Resume Parsing (each resume offloaded to thread pool)
            # =================================================================
            await event_bus.publish(ResumesParsingStartedEvent(
                type=RESUMES_PARSING_STARTED,
                drive_id=drive_id, jd_id=jd_id, total=total_resumes,
            ))

            parsed_resumes  = []
            parse_succeeded = 0
            parse_failed    = 0

            for idx, resume_item in enumerate(payload.resumes, start=1):

                await event_bus.publish(ResumeParsingStartedEvent(
                    type=RESUME_PARSING_STARTED,
                    drive_id=drive_id, jd_id=jd_id,
                    resume_id=resume_item.resumeId, index=idx,
                ))
                parse_start = _now()

                # ── offload blocking parse to thread pool ─────────────────
                result = await loop.run_in_executor(
                    None,
                    partial(
                        self.resume_parser.parse_one,
                        drive_id, jd_id, resume_item, idx, resumes_folder,
                    )
                )

                parse_end = _now()

                await event_bus.publish(ResumeParsingCompletedEvent(
                    type=RESUME_PARSING_COMPLETED,
                    drive_id=drive_id, jd_id=jd_id,
                    resume_id=result["resumeId"],
                    index=result["index"],
                    status=result["status"],
                    resume_dict=result.get("resume_dict"),
                    resume_path=result.get("resume_path"),
                    error=result.get("error"),
                ))

                parsed_resumes.append(result)

                if result["status"] == "success":
                    parse_succeeded += 1
                    summary["resume_parsing"]["completed"] = idx
                    await event_bus.publish(SummaryUpdatedEvent(
                        type=SUMMARY_UPDATED, summary_path=summary_path, summary=summary,
                    ))
                else:
                    parse_failed += 1

                await event_bus.publish(TimingEvent(
                    type=TIMING_EVENT, drive_id=drive_id,
                    label=f"{result.get('filename', resume_item.resumeId)} Parsing",
                    started_at=parse_start, completed_at=parse_end,
                ))

            await event_bus.publish(ResumesParsingCompletedEvent(
                type=RESUMES_PARSING_COMPLETED,
                drive_id=drive_id, jd_id=jd_id,
                total=total_resumes,
                succeeded=parse_succeeded,
                failed=parse_failed,
            ))

            parsed_resume_dicts = [
                r["resume_dict"]
                for r in parsed_resumes
                if r["status"] == "success"
            ]

            # =================================================================
            # STEP 3 — Matching (each match offloaded to thread pool)
            # =================================================================
            await event_bus.publish(ResumesMatchingStartedEvent(
                type=RESUMES_MATCHING_STARTED,
                drive_id=drive_id, jd_id=jd_id,
                total=len(parsed_resume_dicts),
            ))

            matching_results = []
            match_succeeded  = 0
            match_failed     = 0

            for idx, resume_data in enumerate(parsed_resume_dicts, start=1):
                resume_id = resume_data.get("resume_id", f"resume_{idx}")

                await event_bus.publish(ResumeMatchingStartedEvent(
                    type=RESUME_MATCHING_STARTED,
                    drive_id=drive_id, jd_id=jd_id,
                    resume_id=resume_id, index=idx,
                ))
                match_start = _now()

                # ── offload blocking match to thread pool ─────────────────
                try:
                    result = await loop.run_in_executor(
                        None,
                        partial(
                            self.matcher.match_one,
                            resume_dict=resume_data,
                            job_dict=jd_result["job_dict"],
                        )
                    )
                    matching_results.append(result)
                    match_succeeded += 1
                    status = "success"
                    error  = None
                except Exception as exc:
                    logger.warning(f"Matching failed for {resume_id}: {exc}")
                    match_failed += 1
                    status = "failed"
                    error  = str(exc)
                    result = None

                match_end = _now()

                await event_bus.publish(ResumeMatchingCompletedEvent(
                    type=RESUME_MATCHING_COMPLETED,
                    drive_id=drive_id, jd_id=jd_id,
                    resume_id=resume_id, index=idx,
                    status=status,
                    error=error,
                    candidate_result=result.dict() if status == "success" else None,
                    scores_path=str(
                        resumes_folder / resume_id / f"{resume_id}_scores.json"
                    ) if status == "success" else None,
                ))

                summary["jd_resume_matching"]["completed"] = idx
                await event_bus.publish(SummaryUpdatedEvent(
                    type=SUMMARY_UPDATED, summary_path=summary_path, summary=summary,
                ))
                await event_bus.publish(TimingEvent(
                    type=TIMING_EVENT, drive_id=drive_id,
                    label=f"{resume_id} Matching",
                    started_at=match_start, completed_at=match_end,
                ))

            await event_bus.publish(ResumesMatchingCompletedEvent(
                type=RESUMES_MATCHING_COMPLETED,
                drive_id=drive_id, jd_id=jd_id,
                total=len(parsed_resume_dicts),
                succeeded=match_succeeded,
                failed=match_failed,
            ))

            # =================================================================
            # STEP 4 — Ranking (CPU-bound but quick relative to LLM calls;
            #           still offloaded to be safe)
            # =================================================================
            await event_bus.publish(ResumesRankingStartedEvent(
                type=RESUMES_RANKING_STARTED,
                drive_id=drive_id, jd_id=jd_id,
                total=len(matching_results),
            ))

            ranking_result = await loop.run_in_executor(
                None,
                partial(
                    self.matcher.rank_all,
                    drive_id=drive_id,
                    jd_id=jd_id,
                    resumes_folder=resumes_folder,
                    matching_results=matching_results,
                    base_weight=base_weight,
                    additional_weight=additional_weight,
                    preferences=preferences,
                )
            )

            await event_bus.publish(ResumesRankingCompletedEvent(
                type=RESUMES_RANKING_COMPLETED,
                drive_id=drive_id, jd_id=jd_id,
                total=ranking_result["totalCandidates"],
                ranking=ranking_result["ranking"],
            ))

            # =================================================================
            # STEP 5 — Write final result and mark job complete
            # =================================================================
            final_result = {
                "driveId":         drive_id,
                "jdId":            jd_id,
                "status":          "success",
                "totalCandidates": ranking_result["totalCandidates"],
                "ranking":         ranking_result["ranking"],
            }

            final_result_path = job_folder / "result.json"
            with open(final_result_path, "w") as f:
                json.dump(final_result, f, indent=4)

            set_job_flag(drive_id, 1)   # ← signals get_result() it's ready

            await event_bus.publish(JobCompletedEvent(
                type=JOB_COMPLETED, drive_id=drive_id,
                jd_id=jd_id, total_resumes=total_resumes,
            ))

        except Exception as exc:
            # Catch-all so the background task never dies silently.
            logger.exception(f"[{drive_id}] Unhandled error in _process_job: {exc}")
            await event_bus.publish(JobFailedEvent(
                type=JOB_FAILED, drive_id=drive_id,
                jd_id=jd_id, error=str(exc),
            ))
            # Optionally set flag to -1 so the poller can distinguish
            # "failed" from "ongoing":
            set_job_flag(drive_id, -1)

    # ─────────────────────────────────────────────────────────────────────────
    # RESULT POLLING — unchanged from original
    # ─────────────────────────────────────────────────────────────────────────
    def get_result(self, drive_id: str) -> dict:
        flag = get_job_flag(drive_id)

        if flag is None:
            raise HTTPException(status_code=404, detail="Job not found.")

        if flag == 0:
            raise HTTPException(status_code=202, detail="Job accepted and processing")

        if flag == -1:
            raise HTTPException(status_code=500, detail="Job failed. Check logs.")

        result_path = Path(OUTPUT_BASE_DIR) / drive_id / "result.json"
        if not result_path.exists():
            raise HTTPException(status_code=404, detail="Result file not found.")

        return load_json(str(result_path))