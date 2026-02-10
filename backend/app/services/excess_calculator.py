from typing import List, Dict
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job
from app.schemas.matching_result_schema import (
    ExcessMetrics,
    EducationExcessMetrics,
    ExperienceExcessMetrics,
    CertificationExcessMetrics
)
from app.schemas.SkillsExcess import SkillsExcess


class ExcessCalculator:
    """Calculates excess metrics for comparative ranking"""
    
    # ==================== EDUCATION ====================
    
    @staticmethod
    def calculate_education_excess(resume: Resume, job: Job) -> EducationExcessMetrics:
        """Calculate education excess metrics"""
        
        # Count required degrees
        required_degrees = 0
        if job.education_requirements and job.education_requirements.groups:
            for group in job.education_requirements.groups:
                required_degrees += len(group.degrees)
        
        # Count candidate degrees
        candidate_degrees = 0
        degree_levels = []
        if resume.education and resume.education.entries:
            candidate_degrees = len(resume.education.entries)
            degree_levels = [entry.degree_level for entry in resume.education.entries]
        
        # Calculate excess
        excess_count = max(0, candidate_degrees - required_degrees)
        
        # Optional: weighted excess
        DEGREE_WEIGHTS = {
            "diploma": 1,
            "associate": 1,
            "bachelor's": 2,
            "bachelor": 2,
            "master's": 3,
            "master": 3,
            "phd": 4,
            "doctorate": 4,
            "mba": 3
        }
        
        weighted_excess = 0.0
        if degree_levels:
            total_weight = sum(
                DEGREE_WEIGHTS.get(level.lower().strip(), 1) 
                for level in degree_levels
            )
            required_weight = required_degrees * 2  # Assume Bachelor's as baseline
            weighted_excess = max(0.0, total_weight - required_weight)
        
        return EducationExcessMetrics(
            required_degrees=required_degrees,
            candidate_degrees=candidate_degrees,
            excess_count=excess_count,
            degree_levels=degree_levels,
            weighted_excess=weighted_excess
        )
    
    # ==================== SKILLS ====================
    
    @staticmethod
    def calculate_skills_excess(
        resume: Resume, 
        job: Job, 
        matched_skills: List[str],
        total_required_skills: int = 0  # ✅ NEW PARAMETER
    ) -> SkillsExcess:
        """
        Calculate skills excess metrics
        
        Args:
            resume: Candidate's resume
            job: Job requirements
            matched_skills: List of MATCHED REQUIRED skills ONLY
            total_required_skills: Total number of required skills in job
        
        Returns:
            SkillsExcess object with detailed breakdown
        """
        
        # Count total resume skills
        total_resume_skills = 0
        if resume.skills and resume.skills.skills:
            total_resume_skills = len(resume.skills.skills)
        
        # Count required skills (use parameter if provided, else count from job)
        if total_required_skills > 0:
            required_skills_count = total_required_skills  # ✅ Use provided count
        else:
            # Fallback: count from job object
            required_skills_count = 0
            if job.skill_requirements and job.skill_requirements.groups:
                for group in job.skill_requirements.groups:
                    required_skills_count += len(group.skills)
        
        # ✅ matched_skills now contains ONLY the matched required skills
        matched_required_count = len(matched_skills)
        
        # Calculate metrics
        missing_required_count = required_skills_count - matched_required_count
        bonus_skills_count = total_resume_skills - matched_required_count
        
        # Excess count = total resume skills - total required skills
        excess_count = total_resume_skills - required_skills_count
        
        return SkillsExcess(
            required_skills_count=required_skills_count,
            matched_skills_count=total_resume_skills,      # Total skills on resume
            matched_required_count=matched_required_count,  # How many required matched
            missing_required_count=missing_required_count,  # How many required missing
            bonus_skills_count=bonus_skills_count,          # Extra skills beyond required
            excess_count=excess_count                       # Net excess (can be negative)
        )
    
    # ==================== EXPERIENCE ====================
    
    @staticmethod
    def calculate_experience_excess(
        resume: Resume,
        job: Job,
        matched_areas_count: int  # From your experience matching
    ) -> ExperienceExcessMetrics:
        """Calculate experience excess metrics"""
        
        # Get required years (use minimum from range)
        required_years = 0.0
        if job.experience_requirements and job.experience_requirements.groups:
            for group in job.experience_requirements.groups:
                for exp in group.experiences:
                    if exp.min_years:
                        required_years = max(required_years, exp.min_years)
        
        # Get candidate total years
        candidate_years = 0.0
        if resume.experience and resume.experience.experience_areas:
            candidate_years = sum(
                area.total_experience_years or 0.0 
                for area in resume.experience.experience_areas
            )
        
        # Calculate excess years
        excess_years = max(0.0, candidate_years - required_years)
        
        # Count required areas
        required_areas = 0
        if job.experience_requirements and job.experience_requirements.groups:
            for group in job.experience_requirements.groups:
                required_areas += len(group.experiences)
        
        # Excess areas (can be negative if didn't match all)
        excess_areas = matched_areas_count - required_areas
        
        return ExperienceExcessMetrics(
            required_years=required_years,
            candidate_years=candidate_years,
            excess_years=excess_years,
            required_areas=required_areas,
            matched_areas=matched_areas_count,
            excess_areas=excess_areas
        )
    
    # ==================== CERTIFICATIONS ====================
    
    @staticmethod
    def calculate_certification_excess(resume: Resume, job: Job) -> CertificationExcessMetrics:
        """Calculate certification excess metrics"""
        
        # Count required certifications
        required_certs = 0
        if job.certification_requirements and job.certification_requirements.groups:
            for group in job.certification_requirements.groups:
                required_certs += len(group.certifications)
        
        # Count candidate certifications
        candidate_certs = 0
        if resume.certifications and resume.certifications.entries:
            candidate_certs = len(resume.certifications.entries)
        
        # Calculate excess
        excess_count = max(0, candidate_certs - required_certs)
        
        return CertificationExcessMetrics(
            required_certs=required_certs,
            candidate_certs=candidate_certs,
            excess_count=excess_count,
            extra_certs=None
        )
    
    # ==================== COMPLETE EXCESS ====================
    
    @staticmethod
    def calculate_all_excess(
        resume: Resume,
        job: Job,
        matched_skills: List[str],
        matched_areas_count: int,
        total_required_skills: int = 0  # ✅ ADD THIS
    ) -> ExcessMetrics:
        
        skills_excess = ExcessCalculator.calculate_skills_excess(
            resume, 
            job, 
            matched_skills,
            total_required_skills  # ✅ PASS IT HERE
        )
        
        education_excess = ExcessCalculator.calculate_education_excess(resume, job)
        
        experience_excess = ExcessCalculator.calculate_experience_excess(
            resume, 
            job, 
            matched_areas_count
        )
        
        cert_excess = ExcessCalculator.calculate_certification_excess(resume, job)
        
        return ExcessMetrics(
            education=education_excess,
            skills=skills_excess,
            experience=experience_excess,
            certifications=cert_excess
        )