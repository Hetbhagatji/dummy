from fastapi import APIRouter
from app.schemas.job_payload import PrepareJobPayload
from app.services.job_processing.job_processing_service import JobProcessingService

router = APIRouter()
job_processing_service = JobProcessingService()


@router.post("/submit-job/{drive_id}")
async def submit_job(drive_id: str, payload: PrepareJobPayload):
    """
    Accepts job payload and kicks off processing in the background.
    Returns immediately — does NOT wait for processing to finish.
    """
    return await job_processing_service.submit_job(
        drive_id=drive_id, payload=payload
    )


@router.get("/{drive_id}/result")
async def get_job_result(drive_id: str):
    return job_processing_service.get_result(drive_id)
