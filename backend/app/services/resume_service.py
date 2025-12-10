from fastapi import UploadFile,File
from app.utils.file_utils import save_upload_file
from app.services.docling_service import extract_text_from_pdf
from app.prompts.parser_prompt import get_resume_prompt
from  app.schemas.resume_schema import Resume
from app.llm_models.groq_client import call_llm
from app.llm_models.grok_llm import GroqLLM
import json
from app.logger import logger

class ResumeService:
    
    def __init__(self,llm):
        self.llm=llm
    
    def extract_text(self,file: UploadFile) -> dict:
        UPLOAD_DIR = "app/output/uploads"
        file_path = save_upload_file(file, UPLOAD_DIR)
        text = extract_text_from_pdf(file_path)

        return text
        
    def parse_resume(self, file: UploadFile) -> dict:
        try:
            logger.info(f"Resume parsing started for file: {file.filename}")

            UPLOAD_DIR = "app/output/uploads"
            file_path = save_upload_file(file, UPLOAD_DIR)
            logger.info(f"File saved at: {file_path}")

            resume_text = extract_text_from_pdf(file_path)
            logger.info("Text extracted successfully from PDF")

            prompt = get_resume_prompt(resume_text)
            logger.info("Prompt created for LLM")

            llm_response = self.llm.parse(prompt)
            logger.info("LLM response received")

            data = json.loads(llm_response)
            logger.info("LLM response parsed into JSON")

            return Resume(**data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in resume parsing: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in resume parsing: {str(e)}")
            raise

    
    def parse(self,resume_text:str) -> dict:
        prompt = get_resume_prompt(resume_text)

        llm_response = self.llm.parse(prompt)

        data = json.loads(llm_response)

        return Resume(**data)
        