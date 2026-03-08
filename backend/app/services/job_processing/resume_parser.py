import os
import logging
import tempfile
from pathlib import Path

from app.services.s3_service import S3Service
from app.services.resume_service import ResumeService
from app.services.docling_service import extract_text_from_pdf
from app.utils.parse_s3_url import parse_s3_url

logger = logging.getLogger(__name__)


class ResumeParser:
    """
    Pure business logic — downloads resume PDFs, extracts text, parses into Resume dicts.
    Returns data only. No file writing. No RabbitMQ. No event bus.
    """

    def __init__(self, resume_service: ResumeService, s3_service: S3Service):
        self.resume_service = resume_service
        self.s3_service     = s3_service

    def parse_all(self, drive_id: str, jd_id: str, resumes: list, resumes_folder: Path) -> list:
        """
        Returns list of result dicts, one per resume.
        Each dict has: index, resumeId, filename, status, resume_dict/resume_path OR error.
        """
        return [
            self._parse_one(drive_id, jd_id, item, idx, resumes_folder)
            for idx, item in enumerate(resumes, start=1)
        ]

    def _parse_one(
        self,
        drive_id: str,
        jd_id: str,
        resume_item,
        index: int,
        resumes_folder: Path,
    ) -> dict:

        resume_id = resume_item.resumeId
        s3_url    = resume_item.fileUrl
        filename  = Path(s3_url).name
        tmp_path  = None

        local_folder    = resumes_folder / resume_id
        local_folder.mkdir(parents=True, exist_ok=True)
        resume_path = str(local_folder / f"{resume_id}.json")

        try:
            bucket, key = parse_s3_url(s3_url)
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            self.s3_service.download_file_from_bucket(bucket, key, tmp_path)
            resume_text = extract_text_from_pdf(str(tmp_path))
            resume_obj  = self.resume_service.parse(resume_text)

        except Exception as e:
            logger.error({"event": "resume_parse_error", "resume_id": resume_id, "error": str(e)})
            return {
                "index": index, "resumeId": resume_id,
                "filename": filename, "status": "failed", "error": str(e),
            }
        finally:
            if tmp_path and tmp_path.exists():
                try:
                    os.remove(tmp_path)
                except Exception as err:
                    logger.warning({"event": "resume_tmp_cleanup_failed", "error": str(err)})

        resume_dict = resume_obj.dict() if hasattr(resume_obj, "dict") else resume_obj
        resume_dict.update({
            "resume_id":   resume_id,
            "job_id":      drive_id,
            "resume_name": resume_id,
        })

        return {
            "index":       index,
            "resumeId":    resume_id,
            "filename":    filename,
            "status":      "success",
            "resume_dict": resume_obj,
            "resume_path": resume_path,   # caller decides what to do with path
        }