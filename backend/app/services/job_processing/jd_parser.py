import os
import logging
import tempfile
from pathlib import Path

from fastapi import HTTPException

from app.services.s3_service import S3Service
from app.services.job_service import JobService
from app.services.docling_service import extract_text_from_pdf
from app.utils.parse_s3_url import parse_s3_url

logger = logging.getLogger(__name__)


class JDParser:
    """
    Pure business logic — downloads JD PDF, extracts text, parses into Job dict.
    Returns data only. No file writing. No RabbitMQ. No event bus.
    """

    def __init__(self, job_service: JobService, s3_service: S3Service):
        self.job_service = job_service
        self.s3_service  = s3_service

    def parse(
        self,
        drive_id: str,
        jd_id: str,
        jd_s3_url: str,
        job_folder: Path,
    ) -> dict:
        """
        Returns:
            { "status": "success", "job_dict": {...} }
            { "status": "failed",  "error": "..." }
        """
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
            return {"status": "failed", "error": str(e)}

        job_dict = parsed_job.dict() if hasattr(parsed_job, "dict") else parsed_job
        job_dict["job_id"] = drive_id
        job_dict["jd_id"]  = jd_id

        return {
            "status":   "success",
            "job_dict": job_dict,
            "job_path": str(job_folder / "job.json"),   # caller decides what to do with path
        }