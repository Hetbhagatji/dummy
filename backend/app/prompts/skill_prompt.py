from app.schemas.raw_schemas import RawJobData
from app.schemas.job_schema import Job


SKILL_SCHEMA = """
{
  "skill_requirements": {
    "groups": [{
      "group_id": "string|null",
      "operator": "\"AND\"|\"OR\"|\"N_OF\"",
      "min_required": "int|null",
      "mandatory": "boolean",
      "skills": [{
        "skill_name": "string",
        "category": "string|null",
        "min_experience_years": "float|null"
      }]
    }]
  }
}
"""


SKILL_PARSING_RULES = """
SKILL PARSING RULES:

0.Hard filtering
IGNORE: soft skills, behaviors, role titles, general experience, attitudes
-Ignore skills which are not related to technical work

1. SEPARATORS AND LOGIC:
- "or" → OR
- "/" → OR
- "and" → AND

- Comma-separated lists (A, B, C):
  - If introduced by OR context words such as
    "e.g.", "such as", "including", "like", "any of", "one of"
    → operator = OR

  - If explicitly connected using "and"
    → operator = AND



2. SOFTENING / ALTERNATIVES (OR):
- "or similar", "such as", "including", "like", "any of", "one of"


5. REQUIREMENT STRENGTH:
- "must have", "required" → mandatory: true
- "preferred", "nice to have", "plus" → mandatory: false
- Default → mandatory: true


7. EXPERIENCE EXTRACTION:
- Extract min_experience_years ONLY if explicitly mentioned.
- Do NOT infer experience.

8. NORMALIZATION:
- Use clear skill names (e.g., "FastAPI", "LangChain", "MongoDB").
- Do NOT expand abbreviations unless explicitly written.

9. NULL RULE:
- If input is null, empty, or "N/A", output null.
- Do NOT create empty groups.

10. NO INFERENCE RULE (CRITICAL):
- Extract ONLY explicitly mentioned skills.
- Do NOT assume related tools, frameworks, or categories.

CATEGORY CLASSIFICATION RULE:

- The `category` field represents the functional classification
  of a skill, NOT an inferred capability.

- Category assignment is ALLOWED and REQUIRED
  when the skill clearly belongs to a well-known technical class.
  
- Category assignment MUST be based ONLY on the skill name itself.
- Do NOT infer category from job role, surrounding text, or industry.

- If a skill does not clearly map to one category,
  set category = null.
  
Group Id related rule
-group_id must be start with like skill1 then skill2,skill3
"""


def get_skill_parsing_prompt(skills_text: str) -> str:
    return f"""
You are a SKILL REQUIREMENTS PARSER with expert logical grouping capability.

TASK:
Parse the RAW SKILLS TEXT into structured skill requirement groups.

RAW SKILLS TEXT:
{skills_text or 'N/A'}

{SKILL_PARSING_RULES}

EXPERIENCE SEPARATION RULE:
- Role titles combined with years of experience (e.g., "8+ years as DevOps Engineer")
  are EXPERIENCE, not skills.
- DO NOT output role names or years inside skill_requirements.
- Ignore such phrases entirely in this parser.

- This parser is ONLY for TECHNICAL and DOMAIN skills.
- DO NOT extract soft skills, behavioral traits, attitudes, or personality attributes.

OUTPUT REQUIREMENTS:
- Output MUST match this schema exactly:
{SKILL_SCHEMA}


- Output ONLY valid JSON
- No markdown
- No explanation
- No extra fields
"""
