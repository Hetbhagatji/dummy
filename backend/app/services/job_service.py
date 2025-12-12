from app.prompts.job_prompt import get_job_prompt
from app.schemas.job_schema import Job
from app.config.logger import get_logger
import json

# Initialize logger
logger = get_logger("JobService")


class JobService:

    def __init__(self, llm):
        self.llm = llm
        

    # -------------------------------
    # PARSE JOB FROM TEXT
    # -------------------------------
    def parse_job(self, job_text: str) -> Job:
        try:
            logger.info({"event": "parse_job_start"})

            # Create LLM prompt
            prompt = get_job_prompt(job_text)
            logger.info({"event": "job_prompt_created", "job_text_length": len(job_text)})

            # Call LLM
            llm_response = self.llm.parse(prompt)
            logger.info({"event": "llm_response_received", "response_length": len(llm_response)})

            # Parse JSON
            data = json.loads(llm_response)
            logger.info({"event": "job_json_parsed", "keys": list(data.keys())})

            job_obj = Job(**data)
            logger.info({"event": "job_model_created", "job_role": job_obj.job_role})

            return job_obj

        except json.JSONDecodeError as e:
            logger.error({"event": "json_decode_error", "error": str(e)})
            raise

        except Exception as e:
            logger.error({"event": "parse_job_unexpected_error", "error": str(e)})
            raise
