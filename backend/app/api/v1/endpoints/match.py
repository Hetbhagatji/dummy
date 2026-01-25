from fastapi import APIRouter,Body
from app.schemas.resume_schemaa import Resume
from app.schemas.job_schema import Job,MatchingPreferences
from app.services.matching_service import MatchingService
from app.schemas.rank_request_schema import ResumeRankRequest
from app.services.similarity_matcher import SimilarityMatcher
from app.schemas.match_request import MatchRequest
from typing import Any, Dict
from app.services.normalizor import normalize_object
from pydantic import BaseModel
router = APIRouter()
matcher=SimilarityMatcher()

matching_service = MatchingService()

@router.post("/match")
def match_resume_to_job(resume: Resume, job: Job):
    return matching_service.match_resume_to_job(resume, job)

@router.post("/rank")
def rank_resumes(request: ResumeRankRequest):
    return matching_service.rank_resumes(request.resumes, request.job,request.weights)


@router.post("/matchh")
async def match_resume_job(payload:MatchRequest):
    print("FUNCTION ENTERED")
    result = matcher.compute_final_score(payload.resume, payload.job,payload.prefs)
    return {
        "status": "success",
        "data": result,
        "message": f"Match score: {result['final_match']:.2%}"
    }
    
class NormalizeRequest(BaseModel):
    payload: Dict[str, Any]
@router.post("/")
def normalize_payload(request: NormalizeRequest):
    """
    Accepts ANY JSON payload and returns normalized JSON
    """
    normalized = normalize_object(request.payload)
    return {
        "normalized": normalized
    }