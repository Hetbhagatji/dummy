from fastapi import UploadFile, HTTPException
from app.utils.file_utils import save_upload_file
from app.services.docling_service import extract_text_from_pdf
from app.prompts.parser_prompt import get_resume_prompt
from app.schemas.resume_schema.resume_schema import Resume
import json
import re
import os
from datetime import datetime, timezone
from app.config.logger import get_logger
from app.utils.experience_calculator import enrich_work_history
from pathlib import Path
from app.services.s3_service import S3Service
import tempfile
import time

OUTPUT_BASE_DIR = Path("output")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def fmt(dt: datetime) -> str:
    return dt.isoformat()


logger = get_logger("ResumeService")


def clean_llm_json(text: str) -> str:
    text = text.strip()
    match = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if match:
        text = match.group(1).strip()
    return text


class ResumeService:
    def __init__(self, llm):
        self.llm = llm
        self.s3_service = S3Service()

    # -------------------------------
    # EXTRACT TEXT FROM PDF
    # -------------------------------
    def extract_text(self, file: UploadFile) -> str:
        try:
            logger.info({"event": "extract_text_start", "file_name": file.filename})
            UPLOAD_DIR = "app/output/uploads"
            file_path = save_upload_file(file, UPLOAD_DIR)
            logger.info({"event": "file_saved", "file_path": file_path})
            text = extract_text_from_pdf(file_path)
            logger.info({"event": "text_extraction_complete", "file_name": file.filename})
            return text
        except Exception as e:
            logger.error({"event": "extract_text_error", "error": str(e), "file_name": file.filename})
            raise

    # -------------------------------
    # PARSE RESUME FROM FILE
    # -------------------------------
    def parse_resume(self, file: UploadFile) -> Resume:
        llm_response = None
        try:
            logger.info({"event": "parse_resume_start", "file_name": file.filename})
            UPLOAD_DIR = "app/output/uploads"
            file_path = save_upload_file(file, UPLOAD_DIR)
            logger.info({"event": "file_saved", "file_path": file_path})

            resume_text = extract_text_from_pdf(file_path)
            logger.info({"event": "pdf_text_extracted", "file_name": file.filename})

            prompt = get_resume_prompt(resume_text)
            llm_response = self.llm.parse(prompt)
            logger.info({"event": "llm_response_received", "file_name": file.filename})

            cleaned_response = clean_llm_json(llm_response)
            data = json.loads(cleaned_response)

            resume_obj = Resume(**data)
            resume_obj.experience = enrich_work_history(resume_obj.experience)
            resume_obj.raw_text = resume_text
            resume_obj.parsed_date = datetime.now(timezone.utc)
            return resume_obj

        except json.JSONDecodeError as e:
            logger.error({
                "event": "json_decode_error",
                "error": str(e),
                "file_name": file.filename,
                "raw_response": llm_response[:500] if llm_response else None
            })
            raise
        except Exception as e:
            logger.error({"event": "parse_resume_unexpected_error", "error": str(e), "file_name": file.filename})
            raise

    # -------------------------------
    # PARSE RESUME FROM RAW TEXT
    # -------------------------------
    def parse(self, resume_text: str) -> Resume:
        llm_response = None
        try:
            logger.info({"event": "parse_text_resume_start"})
            prompt = get_resume_prompt(resume_text)
            llm_response = self.llm.parse(prompt)
            logger.info({"event": "llm_response_received_for_text"})

            cleaned_response = clean_llm_json(llm_response)
            data = json.loads(cleaned_response)

            resume_obj = Resume(**data)
            logger.info({"event": "resume_model_created_from_text", "resume_name": resume_obj.personal_info.full_name})

            resume_obj.experience = enrich_work_history(resume_obj.experience)
            resume_obj.raw_text = resume_text
            resume_obj.parsed_date = datetime.now(timezone.utc)
            return resume_obj

        except json.JSONDecodeError as e:
            logger.error({"event": "json_decode_error_in_parse", "error": str(e)})
            raise
        except Exception as e:
            logger.error({"event": "parse_text_unexpected_error", "error": str(e)})
            raise

    # ============================================================
    # OPTION 1: S3-BASED (fetch PDFs from S3, save JSON to S3)
    # PDFs must be pre-uploaded manually to S3
    # Route: POST /upload-resumes/{job_id}
    # ============================================================
    def upload_resumes_for_job(self, job_id: str) -> dict:
        """
        S3 flow:
        - Fetches PDFs from S3 bucket under {job_id}/resumes/{resume_name}/
        - Parses each PDF
        - Saves JSON back to same S3 folder
        - Saves JSON locally using SAME FOLDER STRUCTURE

        Final Local Structure:
            output/
            └── JOB123/
                └── resumes/
                    └── resume_1/
                        └── resume_1.json
        """

        job_folder = OUTPUT_BASE_DIR / job_id
        summary_path = job_folder / "summary.json"
        details_path = job_folder / "details.txt"
        local_resumes_folder = job_folder / "resumes"

        if not job_folder.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Job '{job_id}' not found. Run /process-job/{job_id} first."
            )

        # Ensure resumes base folder exists
        local_resumes_folder.mkdir(parents=True, exist_ok=True)

        # ── Discover PDFs in S3 ───────────────────────────────────────
        prefix = f"{job_id}/resumes/"
        response = self.s3_service.list_files(prefix)
        pdf_keys = [obj["Key"] for obj in response if obj["Key"].endswith(".pdf")]

        if not pdf_keys:
            raise HTTPException(
                status_code=404,
                detail=f"No PDFs found in S3 under '{prefix}'. Upload PDFs first."
            )

        with open(summary_path, "r") as f:
            summary = json.load(f)

        total = len(pdf_keys)
        summary["resume_parsing"]["total"] = total
        summary["resume_parsing"]["completed"] = 0

        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)

        results = []

        for index, pdf_key in enumerate(pdf_keys, start=1):

            resume_start = utc_now()
            parse_failed = False
            error_msg = ""
            resume_obj = None
            tmp_path = None

            resume_name = Path(pdf_key).stem
            filename = Path(pdf_key).name

            # 🔥 Create local resume folder
            local_resume_folder = local_resumes_folder / resume_name
            local_resume_folder.mkdir(parents=True, exist_ok=True)

            # Paths
            s3_json_key = f"{job_id}/resumes/{resume_name}/{resume_name}.json"
            local_json_path = local_resume_folder / f"{resume_name}.json"

            try:
                # Create temp file
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                    tmp_path = Path(tmp.name)

                self.s3_service.download_file(pdf_key, tmp_path)

                resume_text = extract_text_from_pdf(str(tmp_path))
                resume_obj = self.parse(resume_text)

                time.sleep(5)

            except Exception as e:
                logger.error({
                    "event": "resume_parse_error",
                    "s3_key": pdf_key,
                    "error": str(e)
                })
                parse_failed = True
                error_msg = str(e)

            finally:
                resume_end = utc_now()

                if tmp_path and tmp_path.exists():
                    try:
                        os.remove(tmp_path)
                    except Exception as cleanup_err:
                        logger.warning({
                            "event": "temp_file_cleanup_failed",
                            "error": str(cleanup_err)
                        })

            # ── If Parsing Successful ─────────────────────────────────
            if not parse_failed and resume_obj is not None:

                resume_dict = (
                    resume_obj.dict()
                    if hasattr(resume_obj, "dict")
                    else resume_obj
                )

                # Upload JSON to S3
                self.s3_service.upload_json(resume_dict, s3_json_key)

                # Save JSON locally in its own folder
                with open(local_json_path, "w", encoding="utf-8") as f:
                    json.dump(resume_dict, f, indent=4, default=str)

                summary["resume_parsing"]["completed"] = index
                with open(summary_path, "w") as f:
                    json.dump(summary, f, indent=4)

                with open(details_path, "a") as f:
                    f.write(
                        f"\n{filename} Parsing Time : {fmt(resume_start)} to {fmt(resume_end)}\n"
                    )

                results.append({
                    "index": index,
                    "filename": filename,
                    "status": "success",
                    "s3_pdf": pdf_key,
                    "s3_json": s3_json_key,
                    "local_json": str(local_json_path)
                })

            else:
                with open(details_path, "a") as f:
                    f.write(
                        f"\n{filename} Parsing Time : {fmt(resume_start)} to {fmt(resume_end)} [FAILED]\n"
                    )

                results.append({
                    "index": index,
                    "filename": filename,
                    "status": "failed",
                    "s3_pdf": pdf_key,
                    "error": error_msg
                })

        return {
            "job_id": job_id,
            "total_uploaded": total,
            "completed": summary["resume_parsing"]["completed"],
            "results": results
    }
   