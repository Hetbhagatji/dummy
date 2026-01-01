from app.schemas.raw_schemas import RawJobData as schema


RAW_JOB_SCHEMA = """
{
  "job_title_text": null,
  "company_details_text": null,
  "industry_text": null,
  "raw_locations_text": null,
  "raw_experience_text": null,
  "raw_education_requirements_text": null,
  "raw_skills_text": null,
  "raw_certifications_text": null,
  "raw_responsibilities_text": null,
  "raw_soft_skills_text": null,
  "raw_salary_text": null
}
"""


def get_raw_extraction_prompt(job_text: str) -> str:
    return f"""
You are a RAW INFORMATION EXTRACTION engine.

Your ONLY task is to extract job-related information EXACTLY as written
in the job description.

For each field in the schema:
- Collect ALL relevant text from the ENTIRE job description, not just the first block.
- If multiple sections exist (e.g., "Requirements", "Preferred", "Nice to have"),
  MERGE their content into the same raw_* field.

Field-specific scope:
- raw_skills_text:
  - Include every mention of technical skills from ALL sections,
    including "Required", "Preferred", "Nice to have", etc.
  - Do NOT stop after the first skill section.
  - Include whole sentence or  point when we extract a skill from sentence or point 
- raw_experience_text:
  - Include all experience requirements, including preferred experience.


CRITICAL JSON RULES:
- Escape all newlines as \\n
- Replace bullet points (●, •, –, —) with "-"
- NEVER repeat the JSON object


Output MUST be a SINGLE valid JSON object with this schema:

{RAW_JOB_SCHEMA}

Use null if information is not mentioned.
Use [] only if the JD explicitly lists items but none are present.

Return ONLY valid JSON.
No markdown. No explanation.

JOB DESCRIPTION:
{job_text}
"""