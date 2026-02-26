from app.embedding_models.embedder import ResumeJobEmbedder
from app.services.normalization.text import TextNormalizer
from app.schemas.resume_schema.certifications_schema import Certifications
from app.schemas.job_schema import CertificationRequirements
from app.raw_extractors.certification_extractor import evaluate_certification_group
from typing import List


class CertificationMatcher:
    def __init__(self, embedder: ResumeJobEmbedder, similarity_threshold: float = 0.6):
        self.embedder = embedder
        self.SIMILARITY_THRESHOLD = similarity_threshold

    def match_certifications(
        self,
        resume_certifications: Certifications,
        job_certifications: CertificationRequirements
    ) -> float:
        """Main certification matching - NO PENALTY"""
        if not job_certifications or not job_certifications.groups:
            return 1.0

        if not resume_certifications or not resume_certifications.entries:
            return 0.0

        resume_texts = []
        for cert in resume_certifications.entries:
            cert_name = cert.certification_name or ""
            text = cert_name.strip()
            if text:
                resume_texts.append(TextNormalizer.normalize(text))

        if not resume_texts:
            return 0.0

        group_results = []
        for group in job_certifications.groups:
            result = evaluate_certification_group(      # ← calls module-level helper
                group,
                resume_texts,
                self.SIMILARITY_THRESHOLD
            )
            group_results.append(result)

        if not group_results:
            return 0.0

        avg_score = sum(g["group_score"] for g in group_results) / len(group_results)
        return float(round(avg_score, 3))