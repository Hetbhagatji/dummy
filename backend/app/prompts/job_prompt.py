from app.schemas.job_schema import Job

def get_job_prompt(job_text: str) -> str:
    schema = Job.schema_json(indent=2)

    return f"""Extract structured job information and return pure JSON.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON
2. No markdown, no explanations
3. Output must match this schema exactly

SCHEMA:
{schema}

DOMAIN STANDARDIZATION RULES (CRITICAL):
- job_domain MUST be exactly ONE value from:
  TECH, PHARMACEUTICAL, SALES, MARKETING, HR,
  FINANCE, QA, OPERATIONS, PRODUCT, DESIGN, OTHER

- company_domain MUST be exactly ONE value from:
  PHARMACEUTICAL, HEALTHCARE, BANKING, FINANCE, IT,
  MANUFACTURING, EDUCATION, RETAIL, ENERGY, OTHER

DOMAIN INTERPRETATION RULES:
- company_domain = industry of the company
- job_domain = functional role of the job
- company_domain and job_domain can be DIFFERENT
- Example:
  Pharmaceutical company hiring Data Analyst →
  company_domain = PHARMACEUTICAL
  job_domain = TECH

SALARY RULES:
- Extract salary text EXACTLY as written
- Infer salary_period as:
  yearly / monthly / hourly
- If unclear → null

GENERAL RULES:
- Missing fields → null
- Empty lists → []
- Do not hallucinate values
- Use UPPERCASE for domains

JOB DESCRIPTION:
---
{job_text}
---

Respond with JSON only:""" 
