from app.schemas.job_schema import Job

def get_job_prompt(job_text: str) -> str:
    schema = Job.schema_json(indent=2)

    return f"""Extract structured job information and return pure JSON.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON
2. Do NOT use markdown or ```json
3. Output must match this schema exactly

SCHEMA:
{schema}

RULES:
- Missing fields → null
- Empty lists → []
- Do not hallucinate values
- Extract text exactly

JOB DESCRIPTION:
---
{job_text}
---

Respond with JSON only:"""
