import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.embedding_models.sentence_embedding_model import SentenceEmbeddingModel
from app.schemas.resume_schema import Resume
from app.schemas.job_schema import Job
from app.schemas.weight_schema import WeightSchema
from app.config.logger import get_logger


class MatchingService:
    def __init__(self):
        self.encoder = SentenceEmbeddingModel()
        self.logger = get_logger("MatchingService")

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
            "job_role": job.job_role
        })

        ranked = []
        for resume in resumes:
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
