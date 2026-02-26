from typing import List,Dict
from app.schemas.job_schema import ExperienceRequirements
from app.schemas.resume_schema.experience_schema import Experience
from app.services.normalization.object import TextNormalizer
from app.schemas.job_schema import Job
from app.embedding_models.embedder import ResumeJobEmbedder
from app.raw_extractors.responsibility_extractor import extract_resume_responsibilities

class ResponsibilityMatcher:
    def __init__(self, embedder: ResumeJobEmbedder, similarity_threshold: float = 0.6):
        self.embedder = embedder
        self.SIMILARITY_THRESHOLD = similarity_threshold
    def match_responsibilities(self, experience: Experience, job: Job) -> float:
        """Match resume responsibilities against job responsibilities"""
        resume_responsibilities = extract_resume_responsibilities(experience)
        job_responsibilities = job.responsibilities

        if not job_responsibilities or not resume_responsibilities:
            return 0.0

        RESPONSIBILITY_THRESHOLD = 0.40
        total = len(job_responsibilities)

        job_vectors = self.embedder.embed_texts(job_responsibilities)
        resume_vectors = self.embedder.embed_texts(resume_responsibilities)

        matched_count = 0
        job_scores = []

        for job_vector in job_vectors:
            best_score = 0.0
            
            for resume_vec in resume_vectors:
                score = self.embedder.cosine_similarity(job_vector, resume_vec)
                best_score = max(score, best_score)
            
            if best_score < RESPONSIBILITY_THRESHOLD:
                best_score = 0.0
            else:
                matched_count += 1
            
            job_scores.append(best_score)

        final_score = sum(job_scores) / total

        return float(round(final_score, 3))