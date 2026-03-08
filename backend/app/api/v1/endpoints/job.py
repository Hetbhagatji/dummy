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

# @router.post("/parse-job")
# def parse_job(job_text: str):
#     return job_service.parse_job(job_text)

# @router.post("/preparee-job/{job_id}")
# def process_job(job_id: str):
#     return job_processing_service.prepare_job(job_id)


# @router.post("/prepare-job")
# def process_job(payload: JobPayload):
#     return job_processing_service.prepare_job_from_s3(payload)

@router.post("/prepare-job/{driveId}")
async def submit_job(driveId: str, payload: PrepareJobPayload):
    """
    POST /prepare-job/{driveId}

    Step 1 — Parse the JD PDF from S3
    Step 2 — Parse all resume PDFs from S3 (one by one, synchronously)

    Returns a combined result with JD parsing status + per-resume results.
    """
    result = await job_processing_service.submit_job(
        drive_id=driveId, payload=payload
    )
    return result

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
