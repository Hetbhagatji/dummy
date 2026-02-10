from app.schemas.raw_schemas import RawJobData
from app.schemas.job_schema import Job


STRUCTURED_JOB_SCHEMA = """
{
  "job_id": null,
  "job_metadata": {
    "job_title": "string",
    "industry": "string",
    "employment_type": "string|null",
    "work_mode": "string|null",
    "location": [{
      "city": "string|null",
      "state": "string|null",
      "country": "string|null"
    }]|null,
    "experience_required_years": {
      "min": "int|null",
      "max": "int|null"
    }|null,
    "posted_date": "string|null"
  },
  "soft_skill_requirements": {
    "skills": ["string"]
  },
  "certification_requirements": {
    "groups": [{
      "group_id": "string|null",
      "operator": "\"AND\"|\"OR\"|\"N_OF\"",
      "min_required": "int|null",
      "mandatory": "boolean",
      "certifications": [{
        "certification_name": "string",
        "issuing_body": "string|null"
      }]
    }]
  },
  "experience_requirements": {
    "groups": [{
      "group_id": "string|null",
      "operator": "\"AND\"|\"OR\"|\"N_OF\"",
      "min_required": "int|null",
      "mandatory": "boolean",
      "experiences": [{
        "experience_area": "string|null",
        "min_years": "float|null",
        "max_years": "float|null",
        "key_technologies":"null| list[str]"
      }]
    }]
  },
  "responsibilities": ["string"]|null,
  "salary": {
    "min_amount": "float|null",
    "max_amount": "float|null",
    "currency": "string|null",
    "period": "string|null",
    "raw_text": "string|null"
  }
}
"""


PARSING_RULES = """
LOGICAL PARSING RULES:

1. SEPARATORS AND THEIR MEANING:
- "or" → OR
- "/" → OR
- "and" → AND
- Comma-separated items imply AND by default,
  EXCEPT in EDUCATION where same-level degrees imply OR.

2. SOFTENING PHRASES (OR):
- "or similar", "such as", "including", "like", "any of", "one of"

3. NESTED STRUCTURE:
"A, B or C" →
Group1: [A] AND
Group2: [B, C] OR

4. MULTIPLE STRUCTURES:
"X / Y, Z, and W" →
Group1: [X, Y] OR
Group2: [Z] AND
Group3: [W] AND

5. REQUIREMENT STRENGTH:
- required / must → mandatory: true
- preferred / nice-to-have → mandatory: false
- default → mandatory: true

6. NULL RULE:
- If RAW block is null or "N/A", output null
- Do NOT create empty groups

7. LINE SPLIT RULE:
- Applies to  EXPERIENCE, CERTIFICATIONS, RESPONSIBILITIES

"""


def get_structured_parsing_prompt(raw_data: RawJobData) -> str:
    return f"""
You are a STRUCTURED JOB PARSER with expert logical grouping capability.

TASK:
Convert RAW job text blocks into structured Job JSON following EXACT rules.

RAW DATA BLOCKS:
[JOBS_TITLE]: {raw_data.job_title_text or 'N/A'}
[LOCATIONS]: {raw_data.raw_locations_text or 'N/A'}
[EXPERIENCE]: {raw_data.raw_experience_text or 'N/A'}
[CERTIFICATIONS]: {raw_data.raw_certifications_text or 'N/A'}
[RESPONSIBILITIES]: {raw_data.raw_responsibilities_text or 'N/A'}
[SOFT_SKILLS]: {raw_data.raw_soft_skills_text or 'N/A'}
[SALARY]: {raw_data.raw_salary_text or 'N/A'}

{PARSING_RULES}

OUTPUT REQUIREMENTS:
- Output MUST be a SINGLE valid JSON
- Must match this schema EXACTLY:

{STRUCTURED_JOB_SCHEMA}

Return ONLY valid JSON.
No markdown.
No explanation.
"""
