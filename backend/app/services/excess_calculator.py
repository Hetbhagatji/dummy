from typing import List, Dict
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job
from app.schemas.matching_result_schema import (
    ExcessMetrics,
    EducationExcessMetrics,
    ExperienceExcessMetrics,
    CertificationExcessMetrics,
)
from app.schemas.SkillsExcess import SkillsExcess


# ──────────────────────────────────────────────────────────────────────────────
#  SINGLE SOURCE OF TRUTH for degree weights.
#  Must stay in sync with ComparativeScorer.DEGREE_WEIGHTS.
#  Higher weight = more valuable degree.
# ──────────────────────────────────────────────────────────────────────────────
DEGREE_WEIGHTS: Dict[str, float] = {
    "diploma":      0.5,
    "associate":    0.5,
    "associate's":  0.5,
    "bachelor":     1.0,
    "bachelor's":   1.0,
    "b.tech":       1.0,
    "b.e":          1.0,
    "be":           1.0,
    "bsc":          1.0,
    "b.sc":         1.0,
    "master":       2.0,
    "master's":     2.0,
    "m.tech":       2.0,
    "msc":          2.0,
    "m.sc":         2.0,
    "mba":          2.0,
    "phd":          3.0,
    "ph.d":         3.0,
    "doctorate":    3.0,
    "doctor":       3.0,
}


class ExcessCalculator:
    """
    Calculates raw excess metrics for comparative ranking.

    These metrics feed into ComparativeScorer, which normalises them
    across the candidate batch and converts them into tiebreaker bonuses.

    Key fixes applied:
      1. Degree deduplication — 5× Bachelor's no longer beats 1× Bachelor's.
      2. Only UNIQUE degree levels are counted; duplicates are dropped.
      3. required_years uses SUM (not MAX) across all required experience areas.
      4. DEGREE_WEIGHTS defined once here and imported by ComparativeScorer.
    """

    # ==================== EDUCATION ====================

    @staticmethod
    def calculate_education_excess(resume: Resume, job: Job) -> EducationExcessMetrics:
        """
        Calculate education excess metrics.

        FIX — Degree deduplication:
            Having 5× Bachelor's is no different from having 1× Bachelor's.
            We deduplicate degree_levels before any weight calculation so that
            only genuinely distinct qualifications contribute to the excess score.

            Example:
                Candidate A: [PhD, Master's, Bachelor's]  → 3 unique → weight 6.0
                Candidate B: [Bachelor's × 5]             → 1 unique → weight 1.0
                Job requires: 1 degree

                A excess_value = 6.0 - 1.0 = 5.0  ✓ (real advantage)
                B excess_value = 1.0 - 1.0 = 0.0  ✓ (no spurious bonus)

        required_degrees counting:
            AND group → every degree in the group counts as required
                        (or min_required if set)
            OR  group → only min_required (default 1) degree from the group
        """

        # ── Count required degrees (operator-aware) ──────────────────────────
        required_degrees = 0
        if job.education_requirements and job.education_requirements.groups:
            for group in job.education_requirements.groups:
                operator = (group.operator or "AND").upper()
                n_degrees = len(group.degrees) if group.degrees else 0

                if operator == "OR":
                    min_req = group.min_required if group.min_required else 1
                    required_degrees += min(min_req, n_degrees)
                else:
                    if group.min_required:
                        required_degrees += min(group.min_required, n_degrees)
                    else:
                        required_degrees += n_degrees

        # ── Collect candidate degree levels ──────────────────────────────────
        raw_degree_levels: List[str] = []
        if resume.education and resume.education.entries:
            raw_degree_levels = [
                entry.degree_level
                for entry in resume.education.entries
                if entry.degree_level
            ]

        candidate_degrees = len(raw_degree_levels)

        # ── FIX: Deduplicate degree levels (preserve highest-value first) ────
        #   Sort by weight descending before deduplication so that if the same
        #   level appears multiple times, the canonical copy is kept.
        seen: set = set()
        unique_degree_levels: List[str] = []
        for level in sorted(
            raw_degree_levels,
            key=lambda l: DEGREE_WEIGHTS.get(l.lower().strip(), 1.0),
            reverse=True,
        ):
            normalized = level.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_degree_levels.append(level)  # keep original casing

        # ── Excess ───────────────────────────────────────────────────────────
        # excess_count based on RAW count (meaningful for "how many degrees held")
        # but weight calculation in ComparativeScorer uses UNIQUE levels only.
        excess_count = candidate_degrees - required_degrees

        return EducationExcessMetrics(
            required_degrees=required_degrees,
            candidate_degrees=candidate_degrees,
            excess_count=excess_count,
            # FIX: store UNIQUE levels so ComparativeScorer weights them correctly
            degree_levels=unique_degree_levels,
        )

    # ==================== SKILLS ====================

    @staticmethod
    def calculate_skills_excess(
        resume: Resume,
        job: Job,
        matched_required_skills: List[str],
        total_required_skills: int = 0,
    ) -> SkillsExcess:
        """
        Calculate skills excess metrics.

        Field semantics:
            required_skills_count  — total required skills in the job
            matched_skills_count   — total skills on the candidate's resume
            matched_required_count — how many required skills the candidate matched
            missing_required_count — required_skills_count - matched_required_count
            bonus_skills_count     — resume skills beyond the required matched ones
            excess_count           — matched_skills_count - required_skills_count
                                     (negative = fewer resume skills than required)
        """

        # ── Total resume skills ───────────────────────────────────────────────
        total_resume_skills = 0
        if resume.skills and resume.skills.skills:
            total_resume_skills = len(resume.skills.skills)

        # ── Total required skills ─────────────────────────────────────────────
        if total_required_skills > 0:
            required_skills_count = total_required_skills
        else:
            required_skills_count = 0
            if job.skill_requirements and job.skill_requirements.groups:
                for group in job.skill_requirements.groups:
                    required_skills_count += len(group.skills)

        # ── Matched / missing / bonus ─────────────────────────────────────────
        matched_required_count = len(matched_required_skills)
        missing_required_count = required_skills_count - matched_required_count
        bonus_skills_count     = total_resume_skills - matched_required_count
        excess_count           = total_resume_skills - required_skills_count

        return SkillsExcess(
            required_skills_count=required_skills_count,
            matched_skills_count=total_resume_skills,
            matched_required_count=matched_required_count,
            missing_required_count=missing_required_count,
            bonus_skills_count=bonus_skills_count,
            excess_count=excess_count,
        )

    # ==================== EXPERIENCE ====================

    @staticmethod
    def calculate_experience_excess(
        resume: Resume,
        job: Job,
        matched_areas_count: int,
    ) -> ExperienceExcessMetrics:
        """
        Calculate experience excess metrics.

        required_years — SUM of min_years across all required experience areas.
            Rationale: each area is an independent requirement.  Using MAX
            under-reports the bar and inflates excess for candidates with
            depth in one area but gaps in others.

            Example: job needs 2 yr AI/ML + 3 yr Data Science
              SUM → required = 5 yr  (correct)
              MAX → required = 3 yr  (wrong — inflates excess)

        candidate_years — sum of total_experience_years across ALL resume areas.
        excess_years    — max(0, candidate_years - required_years)
        excess_areas    — can be negative when required areas are unmatched
        """

        # ── Required years (SUM) and areas ───────────────────────────────────
        required_years = 0.0
        required_areas = 0
        if job.experience_requirements and job.experience_requirements.groups:
            for group in job.experience_requirements.groups:
                for exp in group.experiences:
                    required_areas += 1
                    if exp.min_years:
                        required_years += exp.min_years

        # ── Candidate total years ─────────────────────────────────────────────
        candidate_years = 0.0
        if resume.experience and resume.experience.experience_areas:
            candidate_years = sum(
                area.total_experience_years or 0.0
                for area in resume.experience.experience_areas
            )

        # ── Derived metrics ───────────────────────────────────────────────────
        excess_years = max(0.0, candidate_years - required_years)
        excess_areas = matched_areas_count - required_areas   # can be negative

        return ExperienceExcessMetrics(
            required_years=required_years,
            candidate_years=candidate_years,
            excess_years=excess_years,
            required_areas=required_areas,
            matched_areas=matched_areas_count,
            excess_areas=excess_areas,
        )

    # ==================== CERTIFICATIONS ====================

    @staticmethod
    def calculate_certification_excess(resume: Resume, job: Job) -> CertificationExcessMetrics:
        """
        Calculate certification excess metrics.

        excess_count = candidate_certs - required_certs  (NOT clamped)
        Negative → deficit; ComparativeScorer floors it at 0 for bonus
        (deficits are already penalised by the base scorer).
        """

        # ── Required certifications ───────────────────────────────────────────
        required_certs = 0
        if job.certification_requirements and job.certification_requirements.groups:
            for group in job.certification_requirements.groups:
                if hasattr(group, "certifications") and group.certifications:
                    required_certs += len(group.certifications)

        # ── Candidate certifications ──────────────────────────────────────────
        candidate_certs = 0
        if resume.certifications and resume.certifications.entries:
            candidate_certs = len(resume.certifications.entries)

        excess_count = candidate_certs - required_certs

        return CertificationExcessMetrics(
            required_certs=required_certs,
            candidate_certs=candidate_certs,
            excess_count=excess_count,
            extra_certs=None,
        )

    # ==================== COMPLETE EXCESS ====================

    @staticmethod
    def calculate_all_excess(
        resume: Resume,
        job: Job,
        matched_required_skills: List[str],
        matched_areas_count: int,
        total_required_skills: int = 0,
    ) -> ExcessMetrics:
        """
        Compute all excess metrics for one candidate against one job.

        Args:
            resume:                  Candidate resume.
            job:                     Job posting.
            matched_required_skills: Required skills that the candidate matched.
            matched_areas_count:     Number of required experience areas matched.
            total_required_skills:   Pre-counted required skill total (avoids re-counting).

        Returns:
            ExcessMetrics with education, skills, experience, certifications.
        """
        return ExcessMetrics(
            education=ExcessCalculator.calculate_education_excess(resume, job),
            skills=ExcessCalculator.calculate_skills_excess(
                resume,
                job,
                matched_required_skills,
                total_required_skills,
            ),
            experience=ExcessCalculator.calculate_experience_excess(
                resume,
                job,
                matched_areas_count,
            ),
            certifications=ExcessCalculator.calculate_certification_excess(resume, job),
        )