from fastapi import APIRouter,File,UploadFile,HTTPException
from app.services.job_service import JobService
from app.llm_models.grok_job_llm import GroqJobLLM
from typing import List
import asyncio
# from app.services.job_processing_service import JobProcessingService
from app.schemas.job_payload import PrepareJobPayload
router = APIRouter()
# from app.services.job_process_service import JobProcessingService
from app.services.job_processing.job_processing_service import JobProcessingService
# job_service =JobProcessingService()

# llm_instance = GroqJobLLM()
# job_service = JobService(llm=llm_instance)
# job_service = JobService()
job_processing_service = JobProcessingService()



@router.post("/submit-job/{drive_id}")
async def submit_job(drive_id: str, payload: PrepareJobPayload):
    """
    Accepts job payload and kicks off processing in the background.
    Returns immediately — does NOT wait for processing to finish.
    """
    asyncio.create_task(
        job_processing_service.submit_job(drive_id=drive_id, payload=payload)
    )
    return {
        "driveId": drive_id,
        "status":  "accepted",
        "message": "Job submitted. Poll /jobs/{drive_id}/result for the result.",
    }
    
@router.get("/{drive_id}/result")
async def get_job_result(drive_id: str):
    return job_processing_service.get_result(drive_id)
