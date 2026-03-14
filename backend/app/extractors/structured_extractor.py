import json
from typing import Any
from pydantic import ValidationError
from pathlib import Path
import yaml
from app.llm_models.client import get_groq_client
from app.prompts.job_prompt import get_structured_parsing_prompt
from app.schemas.job_schema import Job
from app.schemas.raw_schemas import RawJobData
from app.utils.clean_json import clean_llm_json

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "llm_config.yml"

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

config = load_config()

MODEL_NAME = config["llamma_model"]
print('the model name is ',MODEL_NAME)



class StructuredJobExtractor:
    def __init__(self, model_name: str = MODEL_NAME):
        self.client = get_groq_client()
        self.model_name = model_name

    def parse(self, raw_data: RawJobData) -> Job:
        prompt = get_structured_parsing_prompt(raw_data)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a precise structured job data parser that follows logical grouping rules exactly."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        content = response.choices[0].message.content
        content = clean_llm_json(content)

        print("----- STRUCTURED LLM OUTPUT -----")
        print(content)
        print("---------------------------------")

        try:
            data: Any = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON returned by LLM: {e}\n\nCONTENT:\n{content}")

        try:
            return Job(**data)
        except ValidationError as e:
            raise ValueError(f"Schema validation failed: {e}")
