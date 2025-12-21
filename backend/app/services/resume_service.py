from fastapi import UploadFile
from app.utils.file_utils import save_upload_file
from app.services.docling_service import extract_text_from_pdf
from app.prompts.parser_prompt import get_resume_prompt
from app.schemas.resume_schema.resume_schema import Resume
import json
from datetime import datetime
from app.config.logger import get_logger
from app.utils.experience_calculator import enrich_work_history

# Initialize logger
logger = get_logger("ResumeService")


class ResumeService:
    def __init__(self, llm):
        self.llm = llm

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
            print(text)
            logger.info({"event": "text_extraction_complete", "file_name": file.filename})

            return text

        except Exception as e:
            logger.error({"event": "extract_text_error", "error": str(e), "file_name": file.filename})
            raise

    # -------------------------------
    # PARSE RESUME FROM FILE
    # -------------------------------
    def parse_resume(self, file: UploadFile) -> Resume:
        try:
            logger.info({"event": "parse_resume_start", "file_name": file.filename})

            UPLOAD_DIR = "app/output/uploads"
            file_path = save_upload_file(file, UPLOAD_DIR)
            logger.info({"event": "file_saved", "file_path": file_path})

            resume_text = extract_text_from_pdf(file_path)
            logger.info({"event": "pdf_text_extracted", "file_name": file.filename})

            prompt = get_resume_prompt(resume_text)
            logger.info({"event": "prompt_created", "file_name": file.filename})

            llm_response = self.llm.parse(prompt)
            logger.info({"event": "llm_response_received", "file_name": file.filename})
            
            data = json.loads(llm_response)
            logger.info({"event": "llm_json_parsed", "file_name": file.filename})

            resume_obj = Resume(**data)
            # logger.info({
            #     "event": "resume_model_created",
            #     "file_name": file.filename,

            # })
            
            # ✅ ENRICH WORK HISTORY WITH EXPERIENCE CALCULATIONS
            resume_obj.work_history = enrich_work_history(resume_obj.work_history)
            # logger.info({
            #     "event": "work_history_enriched",
            #     "file_name": file.filename
            # })
            
            # Optional: Add additional metadata
            resume_obj.raw_text = resume_text
            resume_obj.parsed_date = datetime.now()

            return resume_obj

        except json.JSONDecodeError as e:
            logger.error({
                "event": "json_decode_error",
                "error": str(e),
                "file_name": file.filename,
                "raw_response": llm_response[:500] if 'llm_response' in locals() else None
            })
            raise

        except Exception as e:
            logger.error({
                "event": "parse_resume_unexpected_error",
                "error": str(e),
                "file_name": file.filename
            })
            raise


    # -------------------------------
    # PARSE RESUME FROM RAW TEXT
    # -------------------------------
    def parse(self, resume_text: str) -> Resume:
        try:
            logger.info({"event": "parse_text_resume_start"})

            prompt = get_resume_prompt(resume_text)
            logger.info({"event": "prompt_created_for_text"})

            llm_response = self.llm.parse(prompt)
            logger.info({"event": "llm_response_received_for_text"})

            data = json.loads(llm_response)
            logger.info({"event": "llm_json_parsed_for_text"})

            resume_obj = Resume(**data)
            logger.info({"event": "resume_model_created_from_text", "resume_name": resume_obj.name})
            # ✅ BACKEND EXPERIENCE CALCULATION
            resume_obj.work_history = enrich_work_history(
                resume_obj.work_history
            )
            resume_obj.raw_text=resume_text
            resume_obj.parsed_date=datetime.now()
            return resume_obj

        except json.JSONDecodeError as e:
            logger.error({"event": "json_decode_error_in_parse", "error": str(e)})
            raise

        except Exception as e:
            logger.error({"event": "parse_text_unexpected_error", "error": str(e)})
            raise
