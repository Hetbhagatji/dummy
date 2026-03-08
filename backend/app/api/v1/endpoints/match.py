from fastapi import APIRouter,Body,HTTPException
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job
from app.schemas.matching_preferences import MatchingPreferences
from app.schemas.rank_request_schema import ResumeRankRequest
from app.matching.similarity_matcher import SimilarityMatcher
from app.schemas.match_request import MatchRequest
from typing import Any, Dict
from app.services.normalizor import normalize_object
from pydantic import BaseModel
router = APIRouter()
from typing import List
from app.schemas.matching_result_schema import MatchingResult
from app.services.comparative_scorer import ComparativeScorer
from pathlib import Path
import json
from datetime import datetime, timezone
from app.services.matching_service import MatchingService
matching_service= MatchingService()
OUTPUT_BASE_DIR = Path("output")

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def fmt(dt: datetime) -> str:
    return dt.isoformat()
matcher=SimilarityMatcher()


# @router.post("/match")
# def match_resume_to_job(resume: Resume, job: Job):
#     return matching_service.match_resume_to_job(resume, job)

# @router.post("/rank")
# def rank_resumes(request: ResumeRankRequest):
#     return matching_service.rank_resumes(request.resumes, request.job,request.weights)



@router.post("/rank-candidates/{job_id}", response_model=dict)
async def rank_candidates(
    job_id: str,
    base_weight: float = 0.90,
    additional_weight: float = 0.10,
    preferences: MatchingPreferences = Body(default_factory=MatchingPreferences)
):
    """
    Loads job + resumes from local output/{job_id}/,
    runs matching + ranking, saves scores locally,
    publishes RabbitMQ events per resume + phase events.
    """
    return matching_service.rank_candidates_for_job(
        job_id             = job_id,
        base_weight        = base_weight,
        additional_weight  = additional_weight,
        preferences        = preferences
    )