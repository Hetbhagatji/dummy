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
    
    def rank_candidates_for_job(
    self,
    job_id: str,
    base_weight: float = 0.90,
    additional_weight: float = 0.10,
    preferences: MatchingPreferences = None
) -> dict:
        """
        Local → S3 Hybrid Flow:
        - Reads job.json from local folder: backend/output/{job_id}/job.json
        - Reads resume JSONs from local folder:
            backend/output/{job_id}/resumes/{resume_name}/{resume_name}.json
        - Runs matching + comparative ranking
        - Uploads ONLY {resume_name}_scores.json to S3 bucket
        - Returns full ranking response with file names
        """

        # ─────────────────────────────────────────────────────────────
        # 1️⃣ Load job.json from LOCAL
        # ─────────────────────────────────────────────────────────────
        base_path = os.path.join("output", job_id)
        job_path = os.path.join(base_path, "job.json")

        if not os.path.exists(job_path):
            raise HTTPException(
                status_code=404,
                detail=f"job.json not found locally at '{job_path}'"
            )

        try:
            job_data = self._load_json_from_file(job_path)
            job = Job(**job_data)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load local job.json. Error: {str(e)}"
            )

        # ─────────────────────────────────────────────────────────────
        # 2️⃣ Load all resume JSONs from LOCAL
        # ─────────────────────────────────────────────────────────────
        resumes_dir = os.path.join(base_path, "resumes")

        if not os.path.exists(resumes_dir):
            raise HTTPException(
                status_code=404,
                detail=f"Resumes folder not found at '{resumes_dir}'"
            )

        resumes: List[Resume] = []

        for resume_folder in os.listdir(resumes_dir):
            resume_json_path = os.path.join(
                resumes_dir,
                resume_folder,
                f"{resume_folder}.json"
            )

            if os.path.exists(resume_json_path):
                try:
                    resume_data = self._load_json_from_file(resume_json_path)
                    resume_data["resume_name"] = resume_folder
                    resumes.append(Resume(**resume_data))

                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to load resume '{resume_folder}'. Error: {str(e)}"
                    )

        if not resumes:
            raise HTTPException(
                status_code=404,
                detail=f"No resume JSON files found locally under '{resumes_dir}'"
            )

        # ─────────────────────────────────────────────────────────────
        # 3️⃣ Run Matching
        # ─────────────────────────────────────────────────────────────
        matching_results: List[MatchingResult] = []

        for resume in resumes:
            result = self.matcher.compute_final_score_with_excess(resume, job)
            matching_results.append(result)

        # ─────────────────────────────────────────────────────────────
        # 4️⃣ Rank Candidates
        # ─────────────────────────────────────────────────────────────
        ranked_candidates, norm_stats = ComparativeScorer.rank_candidates(
            matching_results,
            base_weight=base_weight,
            additional_weight=additional_weight,
            category_weights=preferences.to_category_weights() if preferences else None
        )

        # ─────────────────────────────────────────────────────────────
        # 5️⃣ Upload ONLY category_scores to S3
        # ─────────────────────────────────────────────────────────────
        for candidate in ranked_candidates:

            resume_name = candidate.candidate_id

            scores_s3_key = f"{job_id}/resumes/{resume_name}/{resume_name}_scores.json"

            category_scores = (
                candidate.category_scores.dict()
                if candidate.category_scores and hasattr(candidate.category_scores, "dict")
                else candidate.category_scores
            )

            scores_payload = {
                "resume_name": resume_name,
                "job_id": job_id,
                "rank": candidate.rank,
                "category_scores": category_scores
            }

            try:
                self.s3_service.upload_json(scores_payload, scores_s3_key)
            except Exception as e:
                self.logger.warning({
                    "event": "scores_upload_failed",
                    "resume_name": resume_name,
                    "error": str(e)
                })

        # ─────────────────────────────────────────────────────────────
        # 6️⃣ Return Full Ranking Response with File Names
        # ─────────────────────────────────────────────────────────────
        return {
            "total_candidates": len(ranked_candidates),
            "job_id": job_id,
            "ranking": [
                {
                    "rank": candidate.rank,
                    "resume_json": f"{candidate.candidate_id}/{candidate.candidate_id}.json",
                    "scores_json": f"{candidate.candidate_id}_scores.json",
                    "base_scores": candidate.base_scores.dict(),
                    "category_scores": candidate.category_scores.dict() if candidate.category_scores else None,
                    "final_base_score": candidate.final_base_score,
                    "final_comparative_score": candidate.final_comparative_score,
                    "excess_metrics": candidate.excess_metrics.dict()
                }
                for candidate in ranked_candidates
            ]
        }

    def _load_json_from_file(self, file_path: str):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)