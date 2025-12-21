from typing import List
from app.schemas.resume_schemaa import Resume
from app.schemas.job_schema import Job
from app.config.logger import get_logger


class ResumeFilterService:
    def __init__(self):
        self.logger = get_logger("ResumeFilterService")

    def filter_by_domain(
        self,
        resumes: List[Resume],
        job: Job
    ) -> List[Resume]:
        """
        Filters resumes strictly based on job_domain vs resume_domain.
        """

        self.logger.info({
            "event": "domain_filter_start",
            "total_resumes": len(resumes),
            "job_domain": job.job_domain
        })

        # If job_domain is missing, return all resumes (fail-safe)
        if not job.job_domain:
            self.logger.warning({
                "event": "job_domain_missing",
                "action": "skipping_domain_filter"
            })
            return resumes

        filtered_resumes = []

        for resume in resumes:
            if not resume.resume_domain:
                continue

            if resume.resume_domain.upper() == job.job_domain.upper():
                filtered_resumes.append(resume)

        self.logger.info({
            "event": "domain_filter_complete",
            "matched_resumes": len(filtered_resumes),
            "job_domain": job.job_domain
        })

        return filtered_resumes
