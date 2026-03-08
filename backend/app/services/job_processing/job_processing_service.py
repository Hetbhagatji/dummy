import logging
from pathlib import Path
from fastapi import HTTPException
from app.services.s3_service import S3Service
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from app.schemas.job_payload import PrepareJobPayload
from app.schemas.matching_preferences import MatchingPreferences

from app.llm_models.llm_factory import get_llm
from app.services.job_processing.jd_parser import JDParser
from app.services.job_processing.resume_parser import ResumeParser
from app.services.job_processing.matcher import MatchingOrchestrator
from app.events.register_handlers import register_all_handlers
from app.utils.set_flag import get_job_flag
from app.utils.load_json import load_json

from app.events.event_bus import event_bus
from app.events.events_types import (
    JOB_STARTED, JOB_FAILED, JOB_COMPLETED,
    JD_PARSING_STARTED, JD_PARSING_COMPLETED,
    RESUMES_PARSING_STARTED, RESUMES_PARSING_COMPLETED,
    RESUME_PARSING_STARTED, RESUME_PARSING_COMPLETED,
    RESUMES_MATCHING_STARTED, RESUMES_MATCHING_COMPLETED,
    RESUME_MATCHING_STARTED, RESUME_MATCHING_COMPLETED,
    SUMMARY_UPDATED,RESUMES_RANKING_COMPLETED,RESUMES_RANKING_STARTED
)
from app.events.event_models import (
    JobStartedEvent, JobFailedEvent, JobCompletedEvent,
    JdParsingStartedEvent, JdParsingCompletedEvent,
    ResumesParsingStartedEvent, ResumesParsingCompletedEvent,
    ResumeParsingStartedEvent, ResumeParsingCompletedEvent,
    ResumesMatchingStartedEvent, ResumesMatchingCompletedEvent,
    ResumeMatchingStartedEvent, ResumeMatchingCompletedEvent,
    SummaryUpdatedEvent,ResumesRankingStartedEvent,ResumesRankingCompletedEvent
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


class JobProcessingService:
    """
    Orchestrator — calls pure parsers/matchers, then emits events.
    No write_json. No publish_event. All side effects handled by listeners.
    """

    def __init__(self):
        s3      = S3Service()
        jobs    = JobService()
        resumes = ResumeService(llm_instance)

        self.jd_parser     = JDParser(jobs, s3)
        self.resume_parser = ResumeParser(resumes, s3)
        self.matcher       = MatchingOrchestrator()

    async def submit_job(
        self,
        drive_id: str,
        payload: PrepareJobPayload,
        base_weight: float = 0.90,
        additional_weight: float = 0.10,
        preferences: MatchingPreferences = None,
    ) -> dict:
        register_all_handlers()

        jd_id         = payload.jd.jdId
        total_resumes = len(payload.resumes)

        job_folder     = OUTPUT_BASE_DIR / drive_id
        resumes_folder = job_folder / "resumes"
        summary_path   = str(job_folder / "summary.json")

        job_folder.mkdir(parents=True, exist_ok=True)
        resumes_folder.mkdir(exist_ok=True)

        summary = {
            "job_id": drive_id, "jd_id": jd_id,
            "jd_parsing": 0,
            "resume_parsing":     {"completed": 0, "total": total_resumes},
            "jd_resume_matching": {"completed": 0, "total": total_resumes},
        }

        # ── Emit: initial summary + job started ───────────────────────────────
        await event_bus.publish(SummaryUpdatedEvent(
            type=SUMMARY_UPDATED, summary_path=summary_path, summary=summary,
        ))
        await event_bus.publish(JobStartedEvent(
            type=JOB_STARTED, drive_id=drive_id, jd_id=jd_id, total_resumes=total_resumes,
        ))

        # =====================================================================
        # STEP 1 — JD Parsing
        # =====================================================================
        await event_bus.publish(JdParsingStartedEvent(
            type=JD_PARSING_STARTED, drive_id=drive_id, jd_id=jd_id,
        ))

        jd_result = self.jd_parser.parse(drive_id, jd_id, payload.jd.fileUrl, job_folder)

        if jd_result["status"] == "failed":
            await event_bus.publish(JobFailedEvent(
                type=JOB_FAILED, drive_id=drive_id, jd_id=jd_id, error=jd_result["error"],
            ))
            return {"driveId": drive_id, "jdId": jd_id,
                    "status": "failed", "error": jd_result["error"]}

        summary["jd_parsing"] = 1
        await event_bus.publish(JdParsingCompletedEvent(
            type=JD_PARSING_COMPLETED,
            drive_id=drive_id,
            jd_id=jd_id,
            job_dict=jd_result["job_dict"],
            job_path=jd_result["job_path"],
        ))
        await event_bus.publish(SummaryUpdatedEvent(
            type=SUMMARY_UPDATED, summary_path=summary_path, summary=summary,
        ))

        # =====================================================================
        # STEP 2 — Resume Parsing
        # =====================================================================
        await event_bus.publish(ResumesParsingStartedEvent(
            type=RESUMES_PARSING_STARTED, drive_id=drive_id, jd_id=jd_id, total=total_resumes,
        ))

        parsed_resumes = self.resume_parser.parse_all(
            drive_id, jd_id, payload.resumes, resumes_folder,
        )

        for result in parsed_resumes:
            await event_bus.publish(ResumeParsingCompletedEvent(
                type=RESUME_PARSING_COMPLETED,
                drive_id=drive_id,
                jd_id=jd_id,
                resume_id=result["resumeId"],
                index=result["index"],
                status=result["status"],
                resume_dict=result.get("resume_dict"),
                resume_path=result.get("resume_path"),
                error=result.get("error"),
            ))
            if result["status"] == "success":
                summary["resume_parsing"]["completed"] = result["index"]
                await event_bus.publish(SummaryUpdatedEvent(
                    type=SUMMARY_UPDATED, summary_path=summary_path, summary=summary,
                ))

        succeeded = sum(1 for r in parsed_resumes if r["status"] == "success")
        failed    = sum(1 for r in parsed_resumes if r["status"] == "failed")

        await event_bus.publish(ResumesParsingCompletedEvent(
            type=RESUMES_PARSING_COMPLETED,
            drive_id=drive_id, jd_id=jd_id,
            total=total_resumes, succeeded=succeeded, failed=failed,
        ))
        
        parsed_resume_dicts = [
            r["resume_dict"]
            for r in parsed_resumes
        ]

        # =====================================================================
        # STEP 3 — Matching (one resume at a time)
        # =====================================================================
        await event_bus.publish(ResumesMatchingStartedEvent(
            type=RESUMES_MATCHING_STARTED,
            drive_id=drive_id, jd_id=jd_id, total=total_resumes,
        ))

        matching_results = []
        match_succeeded  = 0
        match_failed     = 0

        for idx, resume_data in enumerate(parsed_resume_dicts, start=1):
            resume_id = resume_data.get("resume_id", f"resume_{idx}")

            # ── per-resume STARTED ────────────────────────────────────────────
            await event_bus.publish(ResumeMatchingStartedEvent(
                type=RESUME_MATCHING_STARTED,
                drive_id=drive_id, jd_id=jd_id,
                resume_id=resume_id, index=idx,
            ))

            try:
                result = self.matcher.match_all(
                    resume_dicts=[resume_data],      # single resume
                    job_dict=jd_result["job_dict"],
                )[0]                                 # unwrap the one result
                matching_results.append(result)
                match_succeeded += 1
                status = "success"
                error  = None
            except Exception as exc:
                logger.warning(f"Matching failed for {resume_id}: {exc}")
                match_failed += 1
                status = "failed"
                error  = str(exc)

            # ── per-resume COMPLETED ──────────────────────────────────────────
            await event_bus.publish(ResumeMatchingCompletedEvent(
                type=RESUME_MATCHING_COMPLETED,
                drive_id=drive_id, jd_id=jd_id,
                resume_id=resume_id, index=idx,
                status=status,                       # ← add status field
                error=error,                         # ← add error field
                candidate_result=result.dict() if status == "success" else None,
                scores_path=str(
                    resumes_folder / resume_id / f"{resume_id}_scores.json"
                ),
            ))

            summary["jd_resume_matching"]["completed"] = idx
            await event_bus.publish(SummaryUpdatedEvent(
                type=SUMMARY_UPDATED, summary_path=summary_path, summary=summary,
            ))

        await event_bus.publish(ResumesMatchingCompletedEvent(
            type=RESUMES_MATCHING_COMPLETED,
            drive_id=drive_id, jd_id=jd_id,
            total=total_resumes,
            succeeded=match_succeeded,
            failed=match_failed,
        ))

        # =====================================================================
        # STEP 4 — Ranking (all matched results at once)
        # =====================================================================
        await event_bus.publish(ResumesRankingStartedEvent(      # ← NEW
            type=RESUMES_RANKING_STARTED,
            drive_id=drive_id, jd_id=jd_id,
            total=len(matching_results),
        ))

        ranking_result = self.matcher.rank_all(
            drive_id=drive_id,
            jd_id=jd_id,
            resumes_folder=resumes_folder,
            matching_results=matching_results,
            base_weight=base_weight,
            additional_weight=additional_weight,
            preferences=preferences,
        )

        await event_bus.publish(ResumesRankingCompletedEvent(    # ← NEW
            type=RESUMES_RANKING_COMPLETED,
            drive_id=drive_id, jd_id=jd_id,
            total=ranking_result["totalCandidates"],
            ranking=ranking_result["ranking"],
        ))
        
        final_result = {
            "driveId":         drive_id,
            "jdId":            jd_id,
            "status":          "success",
            "totalCandidates": ranking_result["totalCandidates"],
            "ranking":         ranking_result["ranking"],
        }

        final_result_path = job_folder / "result.json"
        with open(final_result_path, "w") as f:
            import json
            json.dump(final_result, f, indent=4)

        # ── Done ─────────────────────────────────────────────────────────────
        await event_bus.publish(JobCompletedEvent(
            type=JOB_COMPLETED, drive_id=drive_id,
            jd_id=jd_id, total_resumes=total_resumes,
        ))
        
        return final_result
    
    def _summary_path(self, drive_id: str) -> Path:
        return Path(OUTPUT_BASE_DIR) / drive_id / "result.json"

    def get_result(self, drive_id: str) -> dict:
        flag = get_job_flag(drive_id)

        if flag is None:
            raise HTTPException(status_code=404, detail="Job not found.")

        if flag == 0:
            raise HTTPException(status_code=409, detail="Process is Ongoing.")

        summary_path = self._summary_path(drive_id)
        if not summary_path.exists():
            raise HTTPException(status_code=404, detail="Result file not found.")

        return load_json(str(summary_path))
    