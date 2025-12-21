from fastapi import APIRouter
from app.schemas.resume_schemaa import Resume
from app.schemas.job_schema import Job
from app.services.matching_service import MatchingService
from app.schemas.rank_request_schema import ResumeRankRequest
router = APIRouter()

matching_service = MatchingService()

@router.post("/match")
def match_resume_to_job(resume: Resume, job: Job):
    return matching_service.match_resume_to_job(resume, job)

@router.post("/rank")
def rank_resumes(request: ResumeRankRequest):
    return matching_service.rank_resumes(request.resumes, request.job,request.weights)