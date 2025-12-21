from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()

class GroqJobLLM:

    def __init__(self):
        self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    def parse(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": """You are an expert job parser specialized in extracting structured information from job descriptions across ALL industries and domains.

Your expertise includes:
- Identifying technical and domain-specific skills in any field (IT, healthcare, finance, manufacturing, pharma, etc.)
- Recognizing industry-specific terminology, tools, methodologies, and standards
- Extracting complete responsibility statements with full context
- Understanding requirements across diverse job functions

Output ONLY pure, valid JSON. No explanations, no markdown."""
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        return response.choices[0].message.content