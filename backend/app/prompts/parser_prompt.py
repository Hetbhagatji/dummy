from app.schemas.resume_schema.resume_schema import Resume


def get_resume_prompt(resume_text: str) -> str:
    schema = Resume.schema_json(indent=2)
    
    # Get current year for duration calculations
    from datetime import datetime
    current_year = datetime.now().year

    return f"""
Extract resume information into JSON that strictly matches the schema below.

CURRENT YEAR: {current_year} (Use this for calculating experience duration when end_year is "current" or "present")

IMPORTANT OUTPUT RULES:
- Return ONLY valid JSON
- No markdown, no explanations
- Output must start with {{ and end with }}
- Use null for missing values
- Use [] for empty lists
- Do NOT invent information

GENERAL GUIDELINES:
- Normalize text lightly (clean titles, standard degree levels)
- Prefer accuracy over completeness

--------------------------------
INDUSTRY DOMAIN IDENTIFICATION
--------------------------------
CRITICAL: Analyze the resume holistically and determine the PRIMARY industry domain:


RULES:
- Look at job titles, company types, skills, and responsibilities
- Choose the MOST PROMINENT domain across their career
- If mixed experience, choose the domain with most recent/longest tenure
- Be specific: prefer "Pharmaceutical" over generic "Healthcare" when appropriate
- If truly ambiguous, use the most recent role's industry


--------------------------------
EDUCATION RULES
--------------------------------
- Each degree must be a separate entry
- Extract degree level only (Bachelor's, Master's, Doctorate, Diploma, Certificate)
- Extract specialization separately in field_of_study
- Order education entries from most recent to oldest
- Use "Present" if education is ongoing
- Do not guess grades or achievements

--------------------------------
WORK EXPERIENCE RULES
--------------------------------
For each work entry:

JOB DETAILS:
- Extract job_title, company_name, location, employment_type
- Extract industry of the company (e.g., if company is "Holy Cross Health", industry is "Healthcare")
- Normalize job titles where obvious (e.g., "Sr." → "Senior")

DATE PARSING (CRITICAL):
- ALL dates must be in YYYY-MM format in the output JSON
- If resume shows "2022", you MUST output "2022-01" 
- If resume shows "Jan 2022" or "January 2022", output "2022-01"
- If resume shows "Dec 2023", output "2023-12"
- Normalize "current", "present", "now", "ongoing" → "current"

EXAMPLES:
  Resume: "2020 - 2023" → Output: "start_date": "2020-01", "end_date": "2023-01"
  Resume: "Mar 2021 - Present" → Output: "start_date": "2021-03", "end_date": "current"
  Resume: "2019" → Output: "start_date": "2019-01", "end_date": "2019-01" (if single date)


RESPONSIBILITIES:
- Extract bullet points as individual list items
- Keep metrics and quantified results if present
- Do not rewrite content



--------------------------------
SKILLS RULES (GLOBAL)
--------------------------------
- Extract skills explicitly stated or clearly demonstrated through responsibilities or achievements
- Support all industries (technical, healthcare, engineering, finance, operations, etc.)
- Deduplicate skills across the entire resume
- Classify skills as:
  - technical_skills → tools, software, systems, methodologies, domain expertise
  - soft_skills → behaviors, collaboration, leadership, communication, teamwork, problem-solving when demonstrated
- Add soft skills only when demonstrated by actions or results, not assumptions
- Do NOT duplicate the same skill in both lists
- Do NOT infer proficiency or experience level unless explicitly stated


--------------------------------
CERTIFICATIONS RULES
--------------------------------
- Extract only formal certifications or licenses
- Include issuing body if present

--------------------------------
FINAL VALIDATION
--------------------------------
- Ensure the JSON exactly matches the schema
- Do not add extra fields
- Do not omit required schema objects
- Verify all total_experience values are calculated correctly
- Verify industry_domain is populated with appropriate domain

SCHEMA:
{schema}

RESUME TEXT:
{resume_text}

OUTPUT (JSON only):
"""