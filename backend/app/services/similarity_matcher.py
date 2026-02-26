from app.embedding_models.embedder import ResumeJobEmbedder
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job, ExperienceRequirements
from typing import Dict, List
from app.schemas.matching_preferences import MatchingPreferences
import numpy as np
from app.services.normalization.object import normalize_object
from app.services.normalization.text import TextNormalizer
from app.schemas.resume_schema.education_schema import Education
from app.schemas.job_schema import EducationRequirements
from app.schemas.resume_schema.certifications_schema import Certifications
from app.schemas.job_schema import CertificationRequirements
from app.schemas.resume_schema.experience_schema import Experience
from app.schemas.resume_schema.skills_schema import Skills
from app.schemas.matching_result_schema import MatchingResult,BaseScores
from app.services.excess_calculator import ExcessCalculator

# DEGREE_LEVEL_RANK = {
#     "diploma": 1,
#     "associate": 2,
#     "bachelor's": 3,
#     "bachelor": 3,
#     "master": 4,
#     "master's": 4,
#     "phd": 5,
#     "doctorate": 5
# }

class SimilarityMatcher:
    def __init__(self):
        self.embedder = ResumeJobEmbedder()
        self.SIMILARITY_THRESHOLD = 0.6
        self.FIELD_SIMILARITY_THRESHOLD = 0.65

    

   

    # ==================== FINAL SCORE COMPUTATION ====================
    
    def compute_final_score(self, resume: Resume, job: Job, prefs: MatchingPreferences = None) -> Dict:
        """Compute final matching score with FULL experience details"""
        resume = normalize_object(resume)
        job = normalize_object(job)
        
        if prefs is None:
            prefs = MatchingPreferences()
        
        # Calculate individual scores
        experience_result = self.match_experience(job.experience_requirements, resume.experience)
        skills_result = self.match_skills(resume, job)
        scores = {
            "skills": skills_result["score"],
            "experience": experience_result["score"],
            "education": self.match_education(resume.education, job.education_requirements),
            "certifications": self.match_certifications(resume.certifications, job.certification_requirements),
            "responsibilities": self.match_responsibilities(resume.experience, job)
        }
        
        # Weighted final score
        final = (
            scores["skills"] * prefs.skill_match_weight +
            scores["experience"] * prefs.experience_match_weight +
            scores["education"] * prefs.education_match_weight +
            scores["certifications"] * prefs.certification_match_weight +
            scores["responsibilities"] * prefs.responsibilities_match_weight
        )
        
        
        return {
            "scores": scores,
            "skill_details": {
                "resume_skills": self.extract_resume_skills(resume.skills),
                "job_skills": self.extract_job_skills(job.skill_requirements),
            },
            "education_details": {
                "resume_education": self.extract_resume_education(resume.education),
                "job_education": self.extract_job_education(job.education_requirements),
            },
            "**NEW**_experience_details": experience_result,  # ✅ DETAILED MATCHES!
            "certification_details": {
                "resume_certifications": self.extract_resume_certifications(resume.certifications),
                "job_certifications": self.extract_job_certifications(job.certification_requirements),
            },
            "final_match": float(round(final, 3)),
            "accepted": final > 0.7,
            "matched_skills": skills_result["matched_skills"],  # ✅ NEW!
            "total_required": skills_result["total_required"]
        }
    def compute_final_score_with_excess(self, resume: Resume, job: Job, prefs: MatchingPreferences = None) -> MatchingResult:
        # Call existing method
        old_result = self.compute_final_score(resume, job, prefs)
        
        # Extract matched skills list (you'll need to store this from match_skills)
        # ✅ Extract ONLY the matched required skills
        matched_skills = old_result.get("matched_skills", [])
        total_required_skills = old_result.get("total_required", 0)
        exp_details = old_result.get("**NEW**_experience_details", {})
        matched_areas_count = sum(
            1 for detail in exp_details.get("details", []) 
            if detail.get("matched_job") is not None
        )
        
        # Calculate excess metrics
        excess_metrics = ExcessCalculator.calculate_all_excess(
            resume=resume,
            job=job,
            matched_skills=matched_skills,  # ✅ Now contains ONLY matched skills
            matched_areas_count=matched_areas_count,
            total_required_skills=total_required_skills
        )
        
        # Create base scores
        base_scores = BaseScores(
            skills=old_result["scores"]["skills"],
            experience=old_result["scores"]["experience"],
            education=old_result["scores"]["education"],
            certifications=old_result["scores"]["certifications"],
            responsibilities=old_result["scores"]["responsibilities"]
        )
        
        # Create matching result
        result = MatchingResult(
            candidate_id=resume.resume_id or "unknown",
            job_id=job.job_id or "unknown",
            base_scores=base_scores,
            excess_metrics=excess_metrics,
            final_base_score=old_result["final_match"],
            is_qualified=old_result["accepted"],
            matching_preferences=prefs.dict() if prefs else None
        )
        
        return result