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


@router.post("/matchh")
async def match_resume_job(payload:MatchRequest):
    print("FUNCTION ENTERED")
    result = matcher.compute_final_score(payload.resume, payload.job,payload.prefs)
    return {
        "status": "success",
        "data": result,
        # "message": f"Match score: {result['final_match']:.2%}"
    }
    

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
                # "additional_scores": candidate.additional_scores.dict() if candidate.additional_scores else None,
                "category_scores": candidate.category_scores.dict() if candidate.category_scores else None,
                "final_base_score": candidate.final_base_score,
                "final_comparative_score": candidate.final_comparative_score,
                # "is_qualified": candidate.is_qualified,
                "excess_metrics": candidate.excess_metrics.dict()
            }
            for candidate in ranked_candidates
        ],
        # "normalization_stats": norm_stats
    }


# ── NEW: /rank-candidates/{job_id} — loads from disk automatically ───────────
@router.post("/rank-candidates/{job_id}", response_model=dict)
async def rank_candidates_by_job_id(
    job_id: str,
    base_weight: float = 0.90,
    additional_weight: float = 0.10
):
    job_folder     = OUTPUT_BASE_DIR / job_id
    resumes_folder = job_folder / "resumes"
    summary_path   = job_folder / "summary.json"
    details_path   = job_folder / "details.txt"
    job_json_path  = job_folder / "job.json"

    # ── Guard checks ─────────────────────────────────────────────────
    if not job_folder.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found. Run POST /process-job/{job_id} first."
        )
    if not job_json_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"job.json missing for '{job_id}'. Job parsing may have failed."
        )
    if not resumes_folder.exists() or not any(resumes_folder.glob("*.json")):
        raise HTTPException(
            status_code=404,
            detail=f"No parsed resumes found for '{job_id}'. Run POST /upload-resumes/{job_id} first."
        )

    # ── Load job from disk ────────────────────────────────────────────
    with open(job_json_path, "r") as f:
        job_data = json.load(f)
    job = Job(**job_data)

    # ── Load all resumes from disk ────────────────────────────────────
    resume_files = sorted(resumes_folder.glob("*.json"))
    resumes: List[Resume] = []
    for resume_file in resume_files:
        with open(resume_file, "r") as f:
            resume_data = json.load(f)
        resumes.append(Resume(**resume_data))

    total = len(resumes)

    # ── Load summary to update it ─────────────────────────────────────
    with open(summary_path, "r") as f:
        summary = json.load(f)

    summary["jd_resume_matching"]["total"]     = total
    summary["jd_resume_matching"]["completed"] = 0

    # Write immediately so total is visible
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=4)

    # ── Match each resume (with per-resume logs) ──────────────────────
    matcher = SimilarityMatcher()
    matching_results: List[MatchingResult] = []

    for index, resume in enumerate(resumes, start=1):
        match_start = utc_now()

        result = matcher.compute_final_score_with_excess(resume, job)
        matching_results.append(result)

        match_end = utc_now()

        # Update summary after each match
        summary["jd_resume_matching"]["completed"] = index
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=4)

        # Append to details.txt
        resume_name = resume_files[index - 1].name   # e.g. resume_1.json
        with open(details_path, "a") as f:
            f.write(
                f"\n{resume_name} Matching Time : "
                f"{fmt(match_start)} to {fmt(match_end)}\n"
            )

    # ── Rank all candidates ───────────────────────────────────────────
    ranked_candidates, norm_stats = ComparativeScorer.rank_candidates(
        matching_results,
        base_weight=base_weight,
        additional_weight=additional_weight
    )

    # ── Return results ────────────────────────────────────────────────
    return {
        "total_candidates": len(ranked_candidates),
        "job_id": job_id,
        "ranking": [
            {
                "rank":                    candidate.rank,
                "candidate_id":            candidate.candidate_id,
                "base_scores":             candidate.base_scores.dict(),
                "category_scores":         candidate.category_scores.dict() if candidate.category_scores else None,
                "final_base_score":        candidate.final_base_score,
                "final_comparative_score": candidate.final_comparative_score,
                "excess_metrics":          candidate.excess_metrics.dict()
            }
            for candidate in ranked_candidates
        ]
    }

@router.post("/rank-candidates-s3/{job_id}", response_model=dict)
async def rank_candidates_s3(
    job_id: str,
    base_weight: float = 0.90,
    additional_weight: float = 0.10,
    preferences: MatchingPreferences = Body(default_factory=MatchingPreferences)
):
    """
    Loads job + resumes from S3, ranks all candidates,
    and stores category_scores per resume back to S3.
    """
    return matching_service.rank_candidates_for_job(
        job_id=job_id,
        base_weight=base_weight,
        additional_weight=additional_weight,
        preferences=preferences
    )