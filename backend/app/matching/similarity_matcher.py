from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job, ExperienceRequirements
from app.schemas.resume_schema.experience_schema import Experience
from app.schemas.matching_preferences import MatchingPreferences
from app.schemas.matching_result_schema import MatchingResult, BaseScores
from app.services.normalization.object import normalize_object
from app.services.excess_calculator import ExcessCalculator
from app.embedding_models.embedder import ResumeJobEmbedder

from app.matching.matchers.skill_matcher import SkillMatcher
from app.matching.matchers.education_matcher import EducationMatcher
from app.matching.matchers.certification_matcher import CertificationMatcher
from app.matching.matchers.experience_matcher import ExperienceMatcher
from app.matching.matchers.responsibility_matcher import ResponsibilityMatcher

from typing import Dict, Optional


class SimilarityMatcher:
    def __init__(self):
        self.embedder   = ResumeJobEmbedder()
        self.skill      = SkillMatcher(self.embedder)
        self.education  = EducationMatcher(self.embedder)
        self.cert       = CertificationMatcher(self.embedder)
        self.experience = ExperienceMatcher(self.embedder)
        self.resp       = ResponsibilityMatcher(self.embedder)

    # ------------------------------------------------------------------ #
    #  Primary scoring                                                     #
    # ------------------------------------------------------------------ #

    def compute_final_score(
        self,
        resume: Resume,
        job: Job,
        prefs: Optional[MatchingPreferences] = None,
    ) -> Dict:
        resume = normalize_object(resume)
        job    = normalize_object(job)

        if prefs is None:
            prefs = MatchingPreferences()

        experience_result = self.experience.match_experience(
            job.experience_requirements,
            resume.experience,
        )
        skills_result = self.skill.match_skills(resume, job)
        edu_score     = self.education.match_education(
            resume.education,
            job.education_requirements,
        )
        cert_score = self.cert.match_certifications(
            resume.certifications,
            job.certification_requirements,
        )
        resp_score = self.resp.match_responsibilities(resume.experience, job)

        scores = {
            "skills":           skills_result["score"],
            "experience":       experience_result["score"],
            "education":        edu_score,
            "certifications":   cert_score,
            "responsibilities": float(f"{resp_score:.3f}"),
        }

        final = (
              scores["skills"]           * prefs.skill_match_weight
            + scores["experience"]       * prefs.experience_match_weight
            + scores["education"]        * prefs.education_match_weight
            + scores["certifications"]   * prefs.certification_match_weight
            + scores["responsibilities"] * prefs.responsibilities_match_weight
        )

        return {
            "scores": scores,

            # FIX: experience_details must NOT be commented out.
            # compute_final_score_with_excess() reads:
            #   exp_details = base_result.get("experience_details", {})
            # If this key is missing it gets an empty dict → matched_areas_count = 0
            # for every candidate → experience area excess is always wrong.
            "experience_details": experience_result,

            "final_match": float(round(final, 3)),
            "accepted":    final > 0.7,

            # FIX: total_required must NOT be commented out.
            # compute_final_score_with_excess() reads:
            #   total_required_skills = base_result.get("total_required", 0)
            # If this key is missing it always gets 0, causing ExcessCalculator
            # to re-count required skills from the job object using a different
            # code path than the skill matcher — the two counts can disagree,
            # producing incorrect excess_count and missing_required_count values.
            "total_required":  skills_result["total_required"],

            # matched_skills contains ONLY the required skills the candidate matched.
            # This is passed to ExcessCalculator.calculate_skills_excess() as
            # matched_required_skills — do NOT replace with all resume skills.
            "matched_skills":  skills_result["matched_skills"],
        }

    # ------------------------------------------------------------------ #
    #  Score + excess metrics                                              #
    # ------------------------------------------------------------------ #

    def compute_final_score_with_excess(
        self,
        resume: Resume,
        job: Job,
        prefs: Optional[MatchingPreferences] = None,
    ) -> MatchingResult:
        base_result = self.compute_final_score(resume, job, prefs)

        # Required skills count — now correctly populated from skills_result
        matched_skills        = base_result.get("matched_skills", [])
        total_required_skills = base_result.get("total_required", 0)

        # Experience area coverage — correctly populated from experience_details
        exp_details = base_result.get("experience_details", {})
        matched_areas_count = sum(
            1
            for detail in exp_details.get("details", [])
            if detail.get("matched_job") is not None
        )

        excess_metrics = ExcessCalculator.calculate_all_excess(
            resume=resume,
            job=job,
            matched_required_skills=matched_skills,
            matched_areas_count=matched_areas_count,
            total_required_skills=total_required_skills,
        )

        base_scores = BaseScores(
            skills=          base_result["scores"]["skills"],
            experience=      base_result["scores"]["experience"],
            education=       base_result["scores"]["education"],
            certifications=  base_result["scores"]["certifications"],
            responsibilities=base_result["scores"]["responsibilities"],
        )

        return MatchingResult(
            candidate_id=        resume.resume_id or "unknown",
            job_id=              job.job_id or "unknown",
            base_scores=         base_scores,
            excess_metrics=      excess_metrics,
            final_base_score=    base_result["final_match"],
            is_qualified=        base_result["accepted"],
            matching_preferences=prefs.dict() if prefs else None,
        )