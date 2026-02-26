from fastapi import APIRouter,File,UploadFile
from app.services.job_service import JobService
from app.llm_models.grok_job_llm import GroqJobLLM
from typing import List
from app.services.job_processing_service import JobProcessingService

router = APIRouter()

# llm_instance = GroqJobLLM()
# job_service = JobService(llm=llm_instance)
job_service = JobService()
job_processing_service = JobProcessingService()

@router.post("/parse-job")
def parse_job(job_text: str):
    return job_service.parse_job(job_text)

@router.post("/process-job/{job_id}")
def process_job(job_id: str):
    return job_processing_service.process_job(job_id)
    
