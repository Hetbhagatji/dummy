import os
import json
import tempfile
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import HTTPException

from app.schemas.job_payload import PrepareJobPayload
from app.services.job_service import JobService
from app.services.resume_service import ResumeService
from app.services.s3_service import S3Service
from app.services.docling_service import extract_text_from_pdf
from app.services.comparative_scorer import ComparativeScorer
from app.matching.similarity_matcher import SimilarityMatcher
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job
from app.schemas.matching_result_schema import MatchingResult
from app.schemas.matching_preferences import MatchingPreferences
from app.messaging.rabbitmq_publisher import publish_event
from app.messaging import events as ev
from app.messaging import payloads as pl

import yaml
from app.llm_models.llm_factory import get_llm

logger = logging.getLogger(__name__)

OUTPUT_BASE_DIR = Path("output")
OUTPUT_BASE_DIR.mkdir(exist_ok=True)

BASE_DIR    = Path(__file__).resolve().parents[2]
CONFIG_PATH = BASE_DIR / "app" / "config" / "llm_config.yml"

with open(CONFIG_PATH, "r") as f:
    config = yaml.safe_load(f)

llm_instance = get_llm(config["llm_model"])


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def fmt(dt: datetime) -> str:
    return dt.isoformat()

def parse_s3_url(s3_url: str) -> tuple[str, str]:
    s3_url = s3_url.removeprefix("s3://")
    bucket, _, key = s3_url.partition("/")
    return bucket, key


class JobProcessingService:

    def __init__(self):
        self.job_service    = JobService()
        self.resume_service = ResumeService(llm_instance)
        self.s3_service     = S3Service()
        self.matcher        = SimilarityMatcher()

    # =========================================================================
    # PUBLIC — single entry point, full pipeline
    # =========================================================================

    def prepare_job_full(
        self,
        drive_id: str,
        payload: PrepareJobPayload,
        base_weight: float = 0.90,
        additional_weight: float = 0.10,
        preferences: MatchingPreferences = None,
    ) -> dict:
        """
        One driveId → full pipeline:
          1. Parse JD
          2. Parse all resumes
          3. Match + rank all resumes against JD
        Publishes RabbitMQ events at every step.
        """

        jd_id         = payload.jd.jdId
        total_resumes = len(payload.resumes)

        # ── Folder setup ──────────────────────────────────────────────────────
        job_folder     = OUTPUT_BASE_DIR / drive_id
        resumes_folder = job_folder / "resumes"
        summary_path   = job_folder / "summary.json"
        details_path   = job_folder / "details.txt"

        job_folder.mkdir(parents=True, exist_ok=True)
        resumes_folder.mkdir(exist_ok=True)

        summary = {
            "job_id":   drive_id,
            "jd_id":    jd_id,
            "jd_parsing": 0,
            "resume_parsing": {
                "completed": 0,
                "total":     total_resumes,
            },
            "jd_resume_matching": {
                "completed": 0,
                "total":     total_resumes,
            },
        }
        self._write_json(summary_path, summary)

        # ── JOB_STARTED ───────────────────────────────────────────────────────
        publish_event(ev.JOB_STARTED,
            pl.job_started(drive_id, jd_id, total_resumes))

        # =====================================================================
        # STEP 1 — JD Parsing
        # =====================================================================
        publish_event(ev.JD_PARSING_STARTED,
            pl.jd_parsing_started(drive_id, jd_id))

        jd_result = self._parse_jd(
            drive_id     = drive_id,
            jd_id        = jd_id,
            jd_s3_url    = payload.jd.fileUrl,
            job_folder   = job_folder,
            summary      = summary,
            summary_path = summary_path,
            details_path = details_path,
        )

        if jd_result["status"] == "failed":
            publish_event(ev.JOB_FAILED,
                pl.job_failed(drive_id, jd_id, jd_result["error"]))
            return {
                "driveId": drive_id,
                "jdId":    jd_id,
                "status":  "failed",
                "error":   jd_result["error"],
            }

        publish_event(ev.JD_PARSING_COMPLETED,
            pl.jd_parsing_completed(drive_id, jd_id, jd_result["parsed_job"]))

        # =====================================================================
        # STEP 2 — Resume Parsing
        # =====================================================================
        publish_event(ev.RESUMES_PARSING_STARTED,
            pl.resumes_parsing_started(drive_id, jd_id, total_resumes))

        parsed_resumes = self._parse_resumes(
            drive_id       = drive_id,
            jd_id          = jd_id,
            resumes        = payload.resumes,
            resumes_folder = resumes_folder,
            summary        = summary,
            summary_path   = summary_path,
            details_path   = details_path,
        )

        succeeded = sum(1 for r in parsed_resumes if r["status"] == "success")
        failed    = sum(1 for r in parsed_resumes if r["status"] == "failed")

        publish_event(ev.RESUMES_PARSING_COMPLETED,
            pl.resumes_parsing_completed(drive_id, jd_id, total_resumes, succeeded, failed))

        # =====================================================================
        # STEP 3 — Matching + Ranking
        # =====================================================================
        ranking_result = self._match_and_rank(
            drive_id          = drive_id,
            jd_id             = jd_id,
            job_folder        = job_folder,
            resumes_folder    = resumes_folder,
            summary           = summary,
            summary_path      = summary_path,
            base_weight       = base_weight,
            additional_weight = additional_weight,
            preferences       = preferences,
        )

        # ── JOB_COMPLETED ─────────────────────────────────────────────────────
        publish_event(ev.JOB_COMPLETED,
            pl.job_completed(drive_id, jd_id, total_resumes))

        return {
            "driveId":         drive_id,
            "jdId":            jd_id,
            "status":          "success",
            "totalCandidates": ranking_result["totalCandidates"],
            "ranking":         ranking_result["ranking"],
        }

    # =========================================================================
    # PRIVATE — Step 1: Parse JD
    # =========================================================================

    def _parse_jd(
        self,
        drive_id: str,
        jd_id: str,
        jd_s3_url: str,
        job_folder: Path,
        summary: dict,
        summary_path: Path,
        details_path: Path,
    ) -> dict:

        jd_start = utc_now()
        bucket, key = parse_s3_url(jd_s3_url)
        tmp_path = None

        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            self.s3_service.download_file_from_bucket(bucket, key, tmp_path)
            jd_text = extract_text_from_pdf(str(tmp_path))

        except Exception as e:
            logger.error({"event": "jd_download_error", "key": key, "error": str(e)})
            raise HTTPException(status_code=500, detail=f"Failed to download JD: {e}")

        finally:
            if tmp_path and tmp_path.exists():
                try:
                    os.remove(tmp_path)
                except Exception as err:
                    logger.warning({"event": "jd_tmp_cleanup_failed", "error": str(err)})

        try:
            parsed_job = self.job_service.parse_job(jd_text)
        except Exception as e:
            logger.error({"event": "jd_parse_error", "error": str(e)})
            jd_end = utc_now()
            with open(details_path, "w") as f:
                f.write(f"JD Parsing: {fmt(jd_start)} → {fmt(jd_end)} [FAILED]\n")
            return {"status": "failed", "error": str(e)}

        jd_end = utc_now()

        job_dict = parsed_job.dict() if hasattr(parsed_job, "dict") else parsed_job

        # ── Inject job_id + jd_id into stored JSON ────────────────────────────
        job_dict["job_id"] = drive_id
        job_dict["jd_id"]  = jd_id

        self._write_json(job_folder / "job.json", job_dict)

        summary["jd_parsing"] = 1
        self._write_json(summary_path, summary)

        # with open(details_path, "w") as f:
        #     f.write(f"JD Parsing: {fmt(jd_start)} → {fmt(jd_end)}\n")

        return {"status": "success", "parsed_job": job_dict}

    # =========================================================================
    # PRIVATE — Step 2: Parse Resumes
    # =========================================================================

    def _parse_resumes(
        self,
        drive_id: str,
        jd_id: str,
        resumes: list,
        resumes_folder: Path,
        summary: dict,
        summary_path: Path,
        details_path: Path,
    ) -> list:

        results = []

        for index, resume_item in enumerate(resumes, start=1):

            # ── resume_id comes from the payload (filename prefix = resumeId) ─
            resume_id    = resume_item.resumeId
            s3_url       = resume_item.fileUrl
            filename     = Path(s3_url).name
            resume_start = utc_now()
            tmp_path     = None
            parse_failed = False
            error_msg    = ""
            resume_obj   = None

            local_folder    = resumes_folder / resume_id
            local_folder.mkdir(parents=True, exist_ok=True)
            local_json_path = local_folder / f"{resume_id}.json"

            # RESUME_PARSING_STARTED
            publish_event(ev.RESUME_PARSING_STARTED,
                pl.resume_parsing_started(drive_id, jd_id, resume_id, index))

            try:
                bucket, key = parse_s3_url(s3_url)
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = Path(tmp.name)
                self.s3_service.download_file_from_bucket(bucket, key, tmp_path)
                resume_text = extract_text_from_pdf(str(tmp_path))
                resume_obj  = self.resume_service.parse(resume_text)

            except Exception as e:
                logger.error({"event": "resume_parse_error", "resume_id": resume_id, "error": str(e)})
                parse_failed = True
                error_msg    = str(e)

            finally:
                resume_end = utc_now()
                if tmp_path and tmp_path.exists():
                    try:
                        os.remove(tmp_path)
                    except Exception as err:
                        logger.warning({"event": "resume_tmp_cleanup_failed", "error": str(err)})

            if not parse_failed and resume_obj is not None:
                resume_dict = resume_obj.dict() if hasattr(resume_obj, "dict") else resume_obj

                # ── Inject resume_id + job_id into stored JSON ────────────────
                resume_dict["resume_id"] = resume_id
                resume_dict["job_id"]    = drive_id
                resume_dict["resume_name"] = resume_id   # matcher uses resume_name

                with open(local_json_path, "w", encoding="utf-8") as f:
                    json.dump(resume_dict, f, indent=4, default=str)

                summary["resume_parsing"]["completed"] = index
                self._write_json(summary_path, summary)

                # with open(details_path, "a") as f:
                #     f.write(f"\n{filename}: {fmt(resume_start)} → {fmt(resume_end)}\n")

                publish_event(ev.RESUME_PARSING_COMPLETED,
                    pl.resume_parsing_completed(
                        job_id        = drive_id,
                        jd_id         = jd_id,
                        resume_id     = resume_id,
                        index         = index,
                        status        = "success",
                        parsed_resume = resume_dict,
                    ))

                results.append({
                    "index":      index,
                    "resumeId":   resume_id,
                    "filename":   filename,
                    "status":     "success",
                    "local_json": str(local_json_path),
                })

            else:
                with open(details_path, "a") as f:
                    f.write(f"\n{filename}: {fmt(resume_start)} → {fmt(resume_end)} [FAILED]\n")

                publish_event(ev.RESUME_PARSING_COMPLETED,
                    pl.resume_parsing_completed(
                        job_id    = drive_id,
                        jd_id     = jd_id,
                        resume_id = resume_id,
                        index     = index,
                        status    = "failed",
                        error     = error_msg,
                    ))

                results.append({
                    "index":    index,
                    "resumeId": resume_id,
                    "filename": filename,
                    "status":   "failed",
                    "error":    error_msg,
                })

        return results

    # =========================================================================
    # PRIVATE — Step 3: Match + Rank
    # =========================================================================

    def _match_and_rank(
        self,
        drive_id: str,
        jd_id: str,
        job_folder: Path,
        resumes_folder: Path,
        summary: dict,
        summary_path: Path,
        base_weight: float,
        additional_weight: float,
        preferences: MatchingPreferences,
    ) -> dict:

        # ── Load job ──────────────────────────────────────────────────────────
        job_path = job_folder / "job.json"
        try:
            job_data = self._load_json(job_path)
            job      = Job(**job_data)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load job.json: {e}")

        # ── Load resumes from local folder ────────────────────────────────────
        resumes: List[Resume] = []

        for resume_folder in os.listdir(resumes_folder):
            resume_json_path = resumes_folder / resume_folder / f"{resume_folder}.json"
            if resume_json_path.exists():
                try:
                    resume_data = self._load_json(resume_json_path)
                    # resume_name must match folder name (= resumeId) for matcher
                    resume_data["resume_name"] = resume_folder
                    resumes.append(Resume(**resume_data))
                except Exception as e:
                    logger.warning(f"Skipping resume '{resume_folder}': {e}")

        if not resumes:
            raise HTTPException(status_code=404, detail="No parsed resumes found for matching.")

        total_resumes = len(resumes)

        # ── RESUMES_MATCHING_STARTED ──────────────────────────────────────────
        publish_event(ev.RESUMES_MATCHING_STARTED,
            pl.resumes_matching_started(drive_id, jd_id, total_resumes))

        # ── Run matching per resume ───────────────────────────────────────────
        matching_results: List[MatchingResult] = []

        for index, resume in enumerate(resumes, start=1):
            resume_id = resume.resume_id   # = resumeId from payload

            publish_event(ev.RESUME_MATCHING_STARTED,
                pl.resume_matching_started(drive_id, jd_id, resume_id, index))

            result = self.matcher.compute_final_score_with_excess(resume, job)
            matching_results.append(result)

        # ── Rank all candidates ───────────────────────────────────────────────
        ranked_candidates, _ = ComparativeScorer.rank_candidates(
            matching_results,
            base_weight       = base_weight,
            additional_weight = additional_weight,
            category_weights  = preferences.to_category_weights() if preferences else None,
        )

        # ── Publish per-candidate COMPLETED + save scores locally ─────────────
        full_ranking    = []
        completed_count = 0

        for candidate in ranked_candidates:
            resume_id = candidate.candidate_id

            category_scores = (
                candidate.category_scores.dict()
                if candidate.category_scores and hasattr(candidate.category_scores, "dict")
                else candidate.category_scores
            )

            candidate_result = {
                "rank":                  candidate.rank,
                "resumeId":              resume_id,
                "jobId":                 drive_id,
                "jdId":                  jd_id,
                "resumeJson":            f"{resume_id}/{resume_id}.json",
                "scoresJson":            f"{resume_id}_scores.json",
                "baseScores":            candidate.base_scores.dict(),
                "categoryScores":        category_scores,
                "finalBaseScore":        candidate.final_base_score,
                "finalComparativeScore": candidate.final_comparative_score,
                "excessMetrics":         candidate.excess_metrics.dict(),
            }

            full_ranking.append(candidate_result)

            # Save scores locally
            local_scores_path = resumes_folder / resume_id / f"{resume_id}_scores.json"
            local_scores_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_scores_path, "w", encoding="utf-8") as f:
                json.dump(candidate_result, f, indent=4)

            # Update summary
            completed_count += 1
            summary["jd_resume_matching"]["completed"] = completed_count
            self._write_json(summary_path, summary)

            # RESUME_MATCHING_COMPLETED — full candidate payload
            publish_event(ev.RESUME_MATCHING_COMPLETED,
                pl.resume_matching_completed(
                    job_id           = drive_id,
                    jd_id            = jd_id,
                    resume_id        = resume_id,
                    index            = completed_count,
                    candidate_result = candidate_result,
                ))

        # ── RESUMES_MATCHING_COMPLETED — full ranking ─────────────────────────
        publish_event(ev.RESUMES_MATCHING_COMPLETED,
            pl.resumes_matching_completed(drive_id, jd_id, total_resumes, full_ranking))

        return {
            "totalCandidates": len(ranked_candidates),
            "ranking":         full_ranking,
        }

    # =========================================================================
    # UTILS
    # =========================================================================

    @staticmethod
    def _load_json(path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _write_json(path: Path, data: dict) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, default=str)