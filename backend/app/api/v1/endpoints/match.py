from fastapi import APIRouter,Body
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job,MatchingPreferences
from app.services.matching_service import MatchingService
from app.schemas.rank_request_schema import ResumeRankRequest
from app.services.similarity_matcher import SimilarityMatcher
from app.schemas.match_request import MatchRequest
from typing import Any, Dict
from app.services.normalizor import normalize_object
from pydantic import BaseModel
router = APIRouter()
from typing import List
from app.schemas.matching_result_schema import MatchingResult
from app.services.comparative_scorer import ComparativeScorer
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

@router.post("/excess")
async def excess_score(payload:MatchRequest):
    result= matcher.compute_final_score_with_excess(payload.resume,payload.job,payload.prefs)
    return result
    

@router.post("/rank-candidates", response_model=dict)
async def rank_candidates(
    resumes: List[Resume],
    job: Job,
    base_weight: float = 0.90,
    additional_weight: float = 0.10
):
    
    # Initialize matcher
    matcher = SimilarityMatcher()
    
    # STEP 1: Calculate base matching for ALL candidates
    matching_results: List[MatchingResult] = []
    
    for resume in resumes:
        # This returns your existing MatchingResult with base_scores and excess_metrics
        result = matcher.compute_final_score_with_excess(resume, job)
        matching_results.append(result)
    
    # STEP 2: Calculate additional scores & rank
    ranked_candidates, norm_stats = ComparativeScorer.rank_candidates(
        matching_results,
        base_weight=base_weight,
        additional_weight=additional_weight
    )
    
    # STEP 3: Return results
    return {
        "total_candidates": len(ranked_candidates),
        "job_id": job.job_id,
        "ranking": [
            {
                "rank": candidate.rank,
                "candidate_id": candidate.candidate_id,
                "base_scores": candidate.base_scores.dict(),
                "additional_scores": candidate.additional_scores.dict() if candidate.additional_scores else None,
                "category_scores": candidate.category_scores.dict() if candidate.category_scores else None,
                "final_base_score": candidate.final_base_score,
                "final_comparative_score": candidate.final_comparative_score,
                "is_qualified": candidate.is_qualified,
                "excess_metrics": candidate.excess_metrics.dict()
            }
            for candidate in ranked_candidates
        ],
        "normalization_stats": norm_stats
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