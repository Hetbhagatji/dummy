# app/llm_models/groq_llm.py
from .base_llm import BaseLLM
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

class GroqLLM(BaseLLM):
    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def parse(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a resume parser that outputs only JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        return response.choices[0].message.content
