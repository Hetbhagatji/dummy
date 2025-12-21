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
            print(repr(llm_response))
            # Parse JSON
            data = json.loads(llm_response)
            logger.info({"event": "job_json_parsed", "keys": list(data.keys())})

            job_obj = Job(**data)
            job_obj.raw_text=job_text
            # logger.info({"event": "job_model_created", "job_role": job_obj.job_role})

            return job_obj

        except json.JSONDecodeError as e:
            logger.error({"event": "json_decode_error", "error": str(e)})
            raise

        except Exception as e:
            logger.error({"event": "parse_job_unexpected_error", "error": str(e)})
            raise
    
    def parse_skills(self, job_text: str) -> Job:
        try:
           

            # Create LLM prompt
            prompt = """
                Extract ONLY skill_requirements from the job text and return valid JSON matching the SkillRequirements schema.

                OUTPUT RULES:
                - Return ONLY JSON
                - Include ONLY "skill_requirements"
                - Use null for missing values
                - Do not add any other fields

                GROUPING RULES:
                - Each group MUST have a sequential group_id starting from "1"
                - Do not set group_id to null

                OPERATOR RULES:
                - Use OR when you see: "or", "/", "either", "such as", "like", "including", "e.g."
                - Use AND when skills are clearly required together or listed with commas without OR words
                - Use N_OF ONLY when an explicit number is mentioned (e.g., "any 2 of"); set min_required accordingly
                - OR / AND → min_required must be null

                MANDATORY RULES:
                - mandatory = true if text says "required", "must have", "essential"
                - mandatory = false if text says "preferred", "nice to have", "optional", "plus"
                - NEVER mix mandatory true and false in the same group

                SKILL RULES:
                - Extract ONLY job-relevant skills (technical, domain, tools)
                - Do NOT include soft skills
                - Do NOT infer or invent skills
                - Do NOT duplicate experience years unless explicitly tied to the skill
                - Category should be a simple label (e.g., Cloud, DevOps, Programming Language) if obvious, otherwise null

                JOB TEXT:
                {job_text}

                OUTPUT JSON:

            
            """
           

            llm_response = self.llm.parse(prompt)
            print(repr(llm_response))
            logger.info({"event": "llm_response_received", "response_length": len(llm_response)})

            data = json.loads(llm_response)

            job_obj = Job(
                job_id=None,
                job_metadata=None,
                education_requirements=None,
                skill_requirements=None,
                soft_skill_requirements=None,
                certification_requirements=None,
                experience_requirements=None,
                responsibilities=[],
                salary=None,
                raw_text=job_text
            )

            job_obj.skill_requirements = data.get("skill_requirements")

            return job_obj

        except json.JSONDecodeError as e:
            logger.error({"event": "json_decode_error", "error": str(e)})
            raise

        except Exception as e:
            logger.error({"event": "parse_job_unexpected_error", "error": str(e)})
            raise
