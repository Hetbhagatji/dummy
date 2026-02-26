from app.services.normalization.object import TextNormalizer
from app.schemas.job_schema import EducationRequirements
from app.schemas.resume_schema.resume_schema import Education
from typing import List
from app.embedding_models.embedder import ResumeJobEmbedder
from app.raw_extractors.education_extractor import extract_resume_levels,extract_job_levels,check_level_capability,extract_resume_degree_combinations,evaluate_education_group


class EducationMatcher:
    def __init__(self, embedder: ResumeJobEmbedder, similarity_threshold: float = 0.6):
        self.embedder = embedder
        self.SIMILARITY_THRESHOLD = similarity_threshold
        
    def match_education(self, resume_education: Education, job_education: EducationRequirements) -> float:
        """Main education matching: LEVEL FIRST → GROUP LOGIC → NO PENALTY"""
        if not job_education or not job_education.groups:
            return 1.0
        if not resume_education or not resume_education.entries:
            return 0.0
        
        # STEP 1: LEVEL CHECK (Global gate)
        resume_levels = extract_resume_levels(resume_education)
        job_levels = extract_job_levels(job_education)
        
        if not check_level_capability(resume_levels, job_levels):
            return 0.0
        
        # STEP 2: Extract degree combinations (level + field pairs)
        resume_combinations = extract_resume_degree_combinations(resume_education)
        group_results = []

        for group in job_education.groups:
            group_score = evaluate_education_group(group, resume_combinations)
            group_results.append(group_score)

        if not group_results:
            return 0.0
        
        # STEP 3: Average group scores
        avg_score = sum(g["group_score"] for g in group_results) / len(group_results)

        return float(round(avg_score, 3))