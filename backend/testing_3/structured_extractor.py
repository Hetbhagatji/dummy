import json
from typing import Any
from pydantic import ValidationError

from client import get_groq_client
from structured_prompts import get_structured_parsing_prompt
from job_schema import Job
from raw_schemas import RawJobData
from utills import clean_llm_json


class StructuredJobExtractor:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
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
