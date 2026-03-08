import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.embedding_models.sentence_embedding_model import SentenceEmbeddingModel
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job
from app.schemas.weight_schema import WeightSchema
from app.config.logger import get_logger
from app.services.resume_filter_service import ResumeFilterService
from typing import List
from fastapi import HTTPException
from app.schemas.matching_result_schema import MatchingResult
from app.services.comparative_scorer import ComparativeScorer
from app.services.s3_service import S3Service
filter_service=ResumeFilterService()
from app.matching.similarity_matcher import SimilarityMatcher
import os
import json
from app.schemas.matching_preferences import MatchingPreferences
from app.messaging.rabbitmq_publisher import publish_event
from app.messaging import events as ev
from app.messaging import payloads as pl   
class MatchingService:
    def __init__(self):
        self.encoder = SentenceEmbeddingModel()
        self.logger = get_logger("MatchingService")
        self.s3_service = S3Service()
        self.matcher = SimilarityMatcher()

    def safe_join(self, items):
        if not items:
            return ""
        return " ".join([str(i) for i in items if i])

    def compute_similarity(self, text1: str, text2: str) -> float:
        if not text1 or not text2:
            return 0.0

        emb1 = self.encoder.encode(text1)
        emb2 = self.encoder.encode(text2)

        score = cosine_similarity([emb1], [emb2])[0][0]
        return round(float(score), 2)

    def match_resume_to_job(self, resume: Resume, job: Job, weights: WeightSchema) -> dict:

        self.logger.info({
            "event": "match_resume_to_job_start",
            "resume_name": resume.name,
            "job_role": job.job_role
        })

        # Resume text preparation
        experience_text = self.safe_join([
            " ".join(filter(None, [exp.role, exp.description]))
            for exp in (resume.experience or [])
        ])
        education_text = self.safe_join([
            " ".join(filter(None, [edu.degree, edu.institution, edu.graduation_year]))
            for edu in (resume.education or [])
        ])

        summary_text = resume.summary or ""
        location_text = resume.location or ""
        skills_text = self.safe_join(resume.skills or [])
        achievements_text = self.safe_join(resume.achivements or [])

        # Job text preparation
        job_role_text = job.job_role or ""
        job_overview_text = job.job_overview or ""
        job_location_text = job.job_location or ""
        responsibilities_text = self.safe_join(job.responsibilities or [])
        skills_required_text = self.safe_join(job.skills_required or [])

        # Individual similarity scores
        scores = {
            "summary_score": self.compute_similarity(summary_text, job_role_text + " " + job_overview_text),
            "experience_score": self.compute_similarity(experience_text, responsibilities_text),
            "location_score": self.compute_similarity(location_text, job_location_text),
            "skills_score": self.compute_similarity(skills_text, skills_required_text),
            "education_score": self.compute_similarity(education_text, skills_required_text),
            "achievements_score": self.compute_similarity(achievements_text, skills_required_text)
        }

        self.logger.info({
            "event": "similarity_scores",
            "resume": resume.name,
            "scores": scores
        })

        # Weighted final score (0 to 1)
        final_score = (
            scores["summary_score"] * weights.summary_weight +
            scores["experience_score"] * weights.experience_weight +
            scores["skills_score"] * weights.skills_weight +
            scores["education_score"] * weights.education_weight +
            scores["location_score"] * weights.location_weight +
            scores["achievements_score"] * weights.achievements_weight
        )
        final_score = round(final_score, 2)

        self.logger.info({
            "event": "final_score_computed",
            "resume": resume.name,
            "final_score": final_score
        })

        return {
            "scores": scores,
            "final_score": final_score
        }

    def rank_resumes(self, resumes, job, weights):
        self.logger.info({
            "event": "ranking_start",
            "total_resumes": len(resumes),
            "job_role": job.job_role,
            "job_domain": job.job_domain
        })

        # ✅ DOMAIN FILTERING (simple, exact match)
        # filtered_resumes = [
        #     resume for resume in resumes
        #     if resume.resume_domain == job.job_domain
        # ]
        filtered_resumes=filter_service.filter_by_domain(resumes,job)

        self.logger.info({
            "event": "domain_filter_applied",
            "job_domain": job.job_domain,
            "before_filter": len(resumes),
            "after_filter": len(filtered_resumes)
        })

        # If no resumes match domain, stop early
        if not filtered_resumes:
            self.logger.warning({
                "event": "no_resumes_after_domain_filter",
                "job_domain": job.job_domain
            })
            return []

        self.logger.info({
            "event": "weights_received",
            "weights": {
                "summary": weights.summary_weight,
                "experience": weights.experience_weight,
                "skills": weights.skills_weight,
                "education": weights.education_weight,
                "location": weights.location_weight,
                "achievements": weights.achievements_weight
            }
        })

        ranked = []
        for resume in filtered_resumes:
            score_obj = self.match_resume_to_job(resume, job, weights)
            ranked.append({
                "name": resume.name,
                "final_score": score_obj["final_score"],
                "scores": score_obj["scores"]
            })

        ranked.sort(key=lambda x: x["final_score"], reverse=True)

        self.logger.info({
            "event": "ranking_complete",
            "order": [r["name"] for r in ranked]
        })

        return ranked
    
    def _load_json_from_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def rank_candidates_for_job(
        self,
        job_id: str,
        base_weight: float = 0.90,
        additional_weight: float = 0.10,
        preferences: MatchingPreferences = None
    ) -> dict:

        # ── 1. Load job.json ──────────────────────────────────────────────────────
        base_path = os.path.join("output", job_id)
        job_path  = os.path.join(base_path, "job.json")

        if not os.path.exists(job_path):
            raise HTTPException(status_code=404, detail=f"job.json not found at '{job_path}'")

        try:
            job_data = self._load_json_from_file(job_path)
            job      = Job(**job_data)
            jd_id    = job_data.get("jd_id", "")       # pull jdId from job.json
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to load job.json: {e}")

        # ── 2. Load resumes ───────────────────────────────────────────────────────
        resumes_dir = os.path.join(base_path, "resumes")

        if not os.path.exists(resumes_dir):
            raise HTTPException(status_code=404, detail=f"Resumes folder not found at '{resumes_dir}'")

        resumes: List[Resume] = []

        for resume_folder in os.listdir(resumes_dir):
            resume_json_path = os.path.join(resumes_dir, resume_folder, f"{resume_folder}.json")
            if os.path.exists(resume_json_path):
                try:
                    resume_data = self._load_json_from_file(resume_json_path)
                    resume_data["resume_name"] = resume_folder
                    resumes.append(Resume(**resume_data))
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to load resume '{resume_folder}': {e}")

        if not resumes:
            raise HTTPException(status_code=404, detail=f"No resume JSONs found under '{resumes_dir}'")

        # ── 3. Load + init summary.json ───────────────────────────────────────────
        summary_path = os.path.join(base_path, "summary.json")

        if not os.path.exists(summary_path):
            raise HTTPException(status_code=404, detail=f"summary.json not found at '{summary_path}'")

        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)

        total_resumes = len(resumes)
        summary["jd_resume_matching"]["total"]     = total_resumes
        summary["jd_resume_matching"]["completed"] = 0

        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=4)

        # ── 4. Publish RESUMES_MATCHING_STARTED ───────────────────────────────────
        publish_event(ev.RESUMES_MATCHING_STARTED,
            pl.resumes_matching_started(job_id, jd_id, total_resumes))

        # ── 5. Run matching — publish per-resume events ───────────────────────────
        matching_results: List[MatchingResult] = []

        for index, resume in enumerate(resumes, start=1):

            resume_id = resume.resume_name

            # RESUME_MATCHING_STARTED
            publish_event(ev.RESUME_MATCHING_STARTED,
                pl.resume_matching_started(job_id, jd_id, resume_id, index))

            # actual matching
            result = self.matcher.compute_final_score_with_excess(resume, job)
            matching_results.append(result)

        # ── 6. Rank all candidates ────────────────────────────────────────────────
        ranked_candidates, norm_stats = ComparativeScorer.rank_candidates(
            matching_results,
            base_weight=base_weight,
            additional_weight=additional_weight,
            category_weights=preferences.to_category_weights() if preferences else None
        )

        # ── 7. Save scores locally + publish per-resume COMPLETED events ──────────
        completed_count = 0
        full_ranking    = []

        for candidate in ranked_candidates:

            resume_id = candidate.candidate_id

            category_scores = (
                candidate.category_scores.dict()
                if candidate.category_scores and hasattr(candidate.category_scores, "dict")
                else candidate.category_scores
            )

            # ── build the candidate result dict (this is what goes in the event) ──
            candidate_result = {
                "rank":                    candidate.rank,
                "resumeId":                resume_id,
                "resumeJson":              f"{resume_id}/{resume_id}.json",
                "scoresJson":              f"{resume_id}_scores.json",
                "baseScores":              candidate.base_scores.dict(),
                "categoryScores":          category_scores,
                "finalBaseScore":          candidate.final_base_score,
                "finalComparativeScore":   candidate.final_comparative_score,
                "excessMetrics":           candidate.excess_metrics.dict(),
            }

            full_ranking.append(candidate_result)

            # ── Save scores locally ───────────────────────────────────────────────
            local_scores_path = os.path.join(
                "output", job_id, "resumes", resume_id, f"{resume_id}_scores.json"
            )
            os.makedirs(os.path.dirname(local_scores_path), exist_ok=True)

            with open(local_scores_path, "w", encoding="utf-8") as f:
                json.dump(candidate_result, f, indent=4)

            # ── Update summary ────────────────────────────────────────────────────
            completed_count += 1
            summary["jd_resume_matching"]["completed"] = completed_count

            with open(summary_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=4)

            # ── RESUME_MATCHING_COMPLETED — full candidate payload ────────────────
            publish_event(ev.RESUME_MATCHING_COMPLETED,
                pl.resume_matching_completed(
                    job_id           = job_id,
                    jd_id            = jd_id,
                    resume_id        = resume_id,
                    index            = completed_count,
                    candidate_result = candidate_result,   # ← full dict
                ))

        # ── 8. Publish RESUMES_MATCHING_COMPLETED — full ranking ─────────────────
        publish_event(ev.RESUMES_MATCHING_COMPLETED,
            pl.resumes_matching_completed(job_id, jd_id, total_resumes, full_ranking))

        # ── 9. Return response ────────────────────────────────────────────────────
        return {
            "jobId":           job_id,
            "jdId":            jd_id,
            "totalCandidates": len(ranked_candidates),
            "ranking":         full_ranking,
        }