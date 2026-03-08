import os
import logging
from pathlib import Path
from typing import List

from fastapi import HTTPException

from app.matching.similarity_matcher import SimilarityMatcher
from app.services.comparative_scorer import ComparativeScorer
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job
from app.schemas.matching_result_schema import MatchingResult
from app.schemas.matching_preferences import MatchingPreferences
from app.utils.load_json import load_json

logger = logging.getLogger(__name__)


class MatchingOrchestrator:
    def __init__(self):
        self.matcher = SimilarityMatcher()

    # ── Step A: match each resume individually, return list of MatchingResult ──

    def match_all(
        self,
        resume_dicts: list,
        job_dict: dict,
    ) -> list[MatchingResult]:
        """
        Runs SimilarityMatcher on every resume independently.
        Returns one MatchingResult per resume — NO ranking yet.
        Caller emits RESUME_MATCHING_STARTED / COMPLETED around each item.
        """
        results = []
        for resume_data in resume_dicts:
            result = self.matcher.compute_final_score_with_excess(
                resume_data, job_dict
            )
            results.append(result)
        return results

    # ── Step B: rank already-matched results, build the output list ───────────

    def rank_all(
        self,
        drive_id: str,
        jd_id: str,
        resumes_folder: Path,
        matching_results: list[MatchingResult],
        base_weight: float,
        additional_weight: float,
        preferences: MatchingPreferences,
    ) -> dict:
        """
        Accepts already-computed MatchingResult objects, ranks them,
        returns {"totalCandidates": int, "ranking": list}.
        No matching work happens here.
        """
        ranked_candidates, _ = ComparativeScorer.rank_candidates(
            matching_results,
            base_weight       = base_weight,
            additional_weight = additional_weight,
            category_weights  = preferences.to_category_weights() if preferences else None,
        )
        ranking = self._build_ranking(drive_id, jd_id, ranked_candidates, resumes_folder)
        return {"totalCandidates": len(ranked_candidates), "ranking": ranking}

    # ── kept exactly as before ────────────────────────────────────────────────

    def _build_ranking(self, drive_id, jd_id, ranked_candidates, resumes_folder) -> list:
        ranking = []
        for candidate in ranked_candidates:
            resume_id = candidate.candidate_id
            category_scores = (
                candidate.category_scores.dict()
                if candidate.category_scores and hasattr(candidate.category_scores, "dict")
                else candidate.category_scores
            )
            entry = {
                "rank":                  candidate.rank,
                "resumeId":              resume_id,
                "jobId":                 drive_id,
                "jdId":                  jd_id,
                "resumeJson":            f"{resume_id}/{resume_id}.json",
                "scoresJson":            f"{resume_id}_scores.json",
                "baseScores":            candidate.base_scores.dict(),
                "categoryScores":        category_scores,
                "finalBaseScore":        candidate.final_base_score,
                "finalComparativeScore": candidate.final_comparative_score,
                "excessMetrics":         candidate.excess_metrics.dict(),
                "scores_path": str(resumes_folder / resume_id / f"{resume_id}_scores.json"),
            }
            ranking.append(entry)
        return ranking