from fastapi import APIRouter
from app.services.job_service import JobService
from app.llm_models.grok_job_llm import GroqJobLLM

router = APIRouter()

llm_instance = GroqJobLLM()
job_service = JobService(llm=llm_instance)

@router.post("/parse-job")
def parse_job(job_text: str):
    return job_service.parse_job(job_text)
@router.post("/parse-skills")
def parse_skills(job_text: str):
    return job_service.parse_skills(job_text)