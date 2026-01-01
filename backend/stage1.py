"""
Run only Stage 1: Entity Extraction
Takes a job description string and prints the raw JSON output.
"""

from groq import Groq
from het_schema import JobExtraction
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Define Stage 1: Entity Extraction
class Stage1_EntityExtractor:
    def __init__(self, client: Groq):
        self.client = client

    def extract(self, job_text: str) -> dict:
        schema = JobExtraction.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        prompt = f"""
        You are a STRICT JSON extraction engine.

        Your task:
        Extract factual information from the Job Description and output a SINGLE valid JSON
        that EXACTLY conforms to the following JSON Schema.

        JSON SCHEMA:
        {schema_str}

        STRICT RULES:
        - Output ONLY valid JSON
        - No markdown
        - No explanations
        - No comments
        - Do NOT infer logic or operators
        - Do NOT add extra fields
        - Use null if a value is not mentioned
        - Use empty arrays [] when applicable
        - Do NOT invent data

        Job Description:
        {job_text}
        """

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured job data strictly following a JSON schema."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        if not content:
            raise RuntimeError("LLM returned empty content in Stage 1")
        return json.loads(content)


# Example usage: Replace this string with your own job description
job_text = """
Responsibilities:

*	Conduct quality checks on equipment performance

*	Ensure compliance with industry standards

*	Collaborate with cross-functional teams

*	Prepare quotes accurately

*	Execute detail engineering tasks


Role: Production & Manufacturing - Other

Industry Type: Aviation
 
Department: Production, Manufacturing & Engineering

Employment Type: Full Time, Permanent

Role Category: Production & Manufacturing - Other

Education


UG: B.Tech/B.E. in Aviation, Mechanical, Diploma in Mechatronics

Key Skills


Detail Engineering are preferred key skill. Communication Skills, English,Telugu, Documentation,
Quality Check, Quote Preparation, Hindi, Quality Assurance

"""

# Run Stage 1
extractor = Stage1_EntityExtractor(client)
output = extractor.extract(job_text)

# Print Stage 1 output
print("🔍 Stage 1: Raw Entity Extraction Output")
print("=" * 60)
print(json.dumps(output, indent=2))
