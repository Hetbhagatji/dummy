import json
from typing import Any
from pydantic import ValidationError

from app.llm_models.client import get_groq_client
from app.prompts.raw_schema_prompt import get_raw_extraction_prompt
from app.schemas.raw_schemas import RawJobData


def clean_llm_json(content: str) -> str:
    """
    Cleans LLM output by removing markdown fences and extra whitespace.
    Ensures the string is valid JSON before parsing.
    """
    if not content:
        return content

    content = content.strip()

    # Remove markdown fences if present
    if content.startswith("```"):
        content = content.replace("```json", "")
        content = content.replace("```", "")
        content = content.strip()

    return content


class RawJobExtractor:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.client = get_groq_client()
        self.model_name = model_name

    def extract(self, job_text: str) -> RawJobData:
        prompt = get_raw_extraction_prompt(job_text)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You extract raw job data."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        content = response.choices[0].message.content
        content = clean_llm_json(content)

        print("----- RAW LLM OUTPUT -----")
        print(content)
        print("--------------------------")

        try:
            data: Any = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON returned by LLM: {e}\n\nCONTENT:\n{content}")

        try:
            return RawJobData(**data)
        except ValidationError as e:
            raise ValueError(f"Schema validation failed: {e}")
