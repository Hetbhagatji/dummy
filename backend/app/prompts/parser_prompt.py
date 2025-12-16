from app.schemas.resume_schema import Resume

def get_resume_prompt(resume_text: str) -> str:
    schema = Resume.schema_json(indent=2)

    return f"""Extract structured resume information and return a VALID JSON object.

CRITICAL INSTRUCTIONS:
1. Return ONLY valid JSON
2. No markdown, no explanations
3. Start response with {{ and end with }}
4. Output MUST match this schema exactly

SCHEMA:
{schema}

FIELD EXTRACTION RULES:
- Extract text exactly as it appears
- Missing fields → null
- Missing lists → []
- Do NOT hallucinate values
- Ensure JSON is valid and parseable

DOMAIN INFERENCE RULES (IMPORTANT):
- Infer resume_domain from experience, role titles, and skills
- Choose the CLOSEST matching domain from the list below
- If domain is unclear, mixed, or low confidence → use "OTHER"
- resume_domain MUST ALWAYS be present
- Use UPPERCASE only

ALLOWED resume_domain VALUES:
TECH, PHARMACEUTICAL, SALES, MARKETING, HR,
FINANCE, QA, OPERATIONS, PRODUCT, DESIGN, OTHER

MATCHING INTENT:
- resume_domain is used ONLY for filtering before similarity scoring
- Accuracy is preferred, but safety is more important than certainty

VALIDATION:
- Double-check JSON validity before responding
- Ensure resume_domain is one of the allowed values

RESUME TEXT:
---
{resume_text}
---

Respond with JSON only:"""
