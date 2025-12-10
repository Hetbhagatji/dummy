from app.prompts.job_prompt import get_job_prompt
from app.schemas.job_schema import Job
from app.logger import logger
import json

class JobService:

    def __init__(self, llm):
        self.llm = llm

    def parse_job(self, job_text: str) -> Job:
        try:
            logger.info("Job parsing started")

            prompt = get_job_prompt(job_text)
            logger.info("Job prompt created")

            llm_response = self.llm.parse(prompt)
            logger.info("LLM response received")

            data = json.loads(llm_response)
            logger.info("Job JSON parsed successfully")

            return Job(**data)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in job parsing: {str(e)}")
            raise

        except Exception as e:
            logger.error(f"Unexpected error in job parsing: {str(e)}")
            raise
