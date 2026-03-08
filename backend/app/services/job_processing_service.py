import os
import json
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException
import requests
import json
from pathlib import Path
from fastapi import HTTPException
from io import BytesIO
import pdfplumber
from app.utils.job_loader import get_job_text
from app.services.job_service import JobService

OUTPUT_BASE_DIR = Path("output")
OUTPUT_BASE_DIR.mkdir(exist_ok=True)

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def fmt(dt: datetime) -> str:
    """Return ISO 8601 UTC format."""
    return dt.isoformat()


class JobProcessingService:

    def __init__(self):
        self.job_service = JobService()
        
    def prepare_job_from_s3(self, payload):

        job_id = payload.recruitment_drive_id

        # ── Folder setup ─────────────────────────────
        job_folder = OUTPUT_BASE_DIR / job_id
        resumes_folder = job_folder / "resumes"

        job_folder.mkdir(parents=True, exist_ok=True)
        resumes_folder.mkdir(exist_ok=True)

        summary_path = job_folder / "summary.json"
        details_path = job_folder / "details.txt"

        summary = {
            "job_id": job_id,
            "jd_parsing": 0,
            "resume_parsing": {
                "completed": 0,
                "total": len(payload.resumes)
            },
            "jd_resume_matching": {
                "completed": 0,
                "total": len(payload.resumes)
            }
        }

        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)

        # ── Download JD PDF ──────────────────────────
        jd_url = payload.jd.url

        try:
            response = requests.get(jd_url)
            response.raise_for_status()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to download JD: {str(e)}")

        # ── Extract text from PDF ────────────────────
        try:
            pdf_file = BytesIO(response.content)

            text = ""

            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF parsing failed: {str(e)}")

        jd_start = utc_now()

        # ── Parse JD text ────────────────────────────
        try:
            parsed_job = self.job_service.parse_job(text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"JD parsing failed: {str(e)}")

        jd_end = utc_now()

        # ── Save parsed job ──────────────────────────
        job_json_path = job_folder / "job.json"

        with open(job_json_path, "w") as f:
            if hasattr(parsed_job, "dict"):
                json.dump(parsed_job.dict(), f, indent=4)
            else:
                json.dump(parsed_job, f, indent=4)

        # ── Update summary ───────────────────────────
        summary["jd_parsing"] = 1

        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)

        # ── Write details ────────────────────────────
        with open(details_path, "w") as f:
            f.write(f"JD Parsing Time: {fmt(jd_start)} to {fmt(jd_end)}\n")

        return {
            "job_id": job_id,
            "message": "JD downloaded from S3 and parsed successfully",
            "job_folder": str(job_folder)
        }

    def prepare_job(self, job_id: str) -> dict:
        # ── Folder setup ────────────────────────────────────────────
        job_folder    = OUTPUT_BASE_DIR / job_id
        resumes_folder = job_folder / "resumes"
        job_folder.mkdir(parents=True, exist_ok=True)
        resumes_folder.mkdir(exist_ok=True)          # ready for later

        summary_path = job_folder / "summary.json"
        details_path = job_folder / "details.txt"

        # ── Initial summary ──────────────────────────────────────────
        summary = {
            "job_id": job_id,
            "jd_parsing": 0,                          # 0 = not done, 1 = done
            "resume_parsing": {
                "completed": 0,
                "total": 0                            # will be filled on resume upload
            },
            "jd_resume_matching": {
                "completed": 0,
                "total": 0                            # will be filled on matching
            }
        }

        # Write initial summary so status is visible immediately
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)

        # ── Fetch raw job text ───────────────────────────────────────
        job_text = get_job_text(job_id)
        if not job_text:
            raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

        # ── JD Parsing ───────────────────────────────────────────────
        jd_start = utc_now()

        try:
            parsed_job = self.job_service.parse_job(job_text)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"JD parsing failed: {str(e)}")

        jd_end = utc_now()

        # Save parsed job as job.json inside job folder
        job_json_path = job_folder / "job.json"
        with open(job_json_path, "w") as f:
            # parsed_job may be a Pydantic model or dict — handle both
            if hasattr(parsed_job, "dict"):
                json.dump(parsed_job.dict(), f, indent=4)
            else:
                json.dump(parsed_job, f, indent=4)

        # ── Update summary.json → jd_parsing = 1 ────────────────────
        summary["jd_parsing"] = 1
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)

        # ── Write details.txt ────────────────────────────────────────
        with open(details_path, "w") as f:          # "w" → fresh file for this job
            f.write(f"JD Parsing Time: {fmt(jd_start)} to {fmt(jd_end)}\n")

        return {
            "job_id":    job_id,
            "job_folder": str(job_folder),
            "message":   "Job parsed successfully"
        }