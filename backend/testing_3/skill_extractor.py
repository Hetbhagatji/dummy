import json
from typing import Any
from pydantic import ValidationError

from client import get_groq_client
from skill_prompt import get_skill_parsing_prompt
from utills import clean_llm_json


class SkillExtractor:
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        self.client = get_groq_client()
        self.model_name = model_name

    def parse(self, skills_text: str) -> dict:
        prompt = get_skill_parsing_prompt(skills_text)

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise skill requirements parser that follows logical grouping rules exactly."
                },
                {
                    "role": "user",
                    "content": prompt
                },
            ],
            temperature=0,
        )

        content = response.choices[0].message.content
        content = clean_llm_json(content)

        print("----- SKILL PARSER OUTPUT -----")
        print(content)
        print("-------------------------------")

        try:
            data: Any = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON returned by LLM: {e}\n\nCONTENT:\n{content}")

        # NOTE:
        # You can later validate this with a SkillRequirements Pydantic model
        return data
