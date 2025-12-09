from fastapi import UploadFile,File
from app.utils.file_utils import save_upload_file
from app.services.docling_service import extract_text_from_pdf
from app.prompts.parser_prompt import get_resume_prompt
from  app.schemas.resume_schema import Resume
from app.llm_models.groq_client import call_llm
import json

class ResumeService:
    
    def extract_text(self,file: UploadFile) -> dict:
        UPLOAD_DIR = "app/output/uploads"
        file_path = save_upload_file(file, UPLOAD_DIR)
        text = extract_text_from_pdf(file_path)

        return text
        
    def parse_resume(self,file:UploadFile) -> dict:
        UPLOAD_DIR = "app/output/uploads"
        file_path = save_upload_file(file, UPLOAD_DIR)
        resume_text = extract_text_from_pdf(file_path)
        prompt = get_resume_prompt(resume_text)

        llm_response = call_llm(prompt)

        data = json.loads(llm_response)

        return Resume(**data)
    
    def parse(self,resume_text:str) -> dict:
        prompt = get_resume_prompt(resume_text)

        llm_response = call_llm(prompt)

        data = json.loads(llm_response)

        return Resume(**data)
        