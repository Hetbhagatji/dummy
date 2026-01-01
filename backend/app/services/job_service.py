from app.config.logger import get_logger
from app.schemas.job_schema import Job

from app.extractors.extractor import RawJobExtractor
from app.extractors.structured_extractor import StructuredJobExtractor
from app.extractors.skill_extractor import SkillExtractor
from app.extractors.education_extractor import run_education_parser

logger = get_logger("JobService")


class JobService:

    def __init__(self):
        
        self.raw_extractor = RawJobExtractor()
        self.structured_extractor = StructuredJobExtractor()
        self.skill_extractor = SkillExtractor()

    # ---------------------------------
    # PARSE JOB FROM RAW TEXT (API ENTRY)
    # ---------------------------------
    def parse_job(self, job_text: str) -> Job:
        try:
            logger.info({
                "event": "parse_job_start",
                "job_text_length": len(job_text)
            })

            # -------------------------------
            # STAGE 1: RAW EXTRACTION
            # -------------------------------
            raw_data = self.raw_extractor.extract(job_text)

            logger.info({"event": "raw_extraction_completed"})

            # -------------------------------
            # STAGE 2: CORE STRUCTURED PARSING
            # -------------------------------
            job = self.structured_extractor.parse(raw_data)

            logger.info({
                "event": "structured_parsing_completed",
                "job_title": job.job_metadata.job_title if job.job_metadata else None
            })

            # -------------------------------
            # STAGE 3: SKILL EXTRACTION
            # -------------------------------
            if raw_data.raw_skills_text:
                skill_data = self.skill_extractor.parse(raw_data.raw_skills_text)
                job.skill_requirements = skill_data.get("skill_requirements")

                logger.info({"event": "skill_parsing_completed"})

            # -------------------------------
            # STAGE 4: EDUCATION EXTRACTION
            # -------------------------------
            if raw_data.raw_education_requirements_text:
                education_data = run_education_parser(
                    raw_data.raw_education_requirements_text
                )
                job.education_requirements = education_data.get("education_requirements")

                logger.info({"event": "education_parsing_completed"})

            return job

        except Exception as e:
            logger.error({
                "event": "parse_job_failed",
                "error": str(e)
            })
            raise
