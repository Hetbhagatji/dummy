def create_job_parser_system_prompt(job_text: str) -> str:
    """Return the global system prompt for the job description parser."""
    return f"""
You are a job description parsing expert. Your task is to extract and structure job requirements from the job description into a structured format.

Schema Rules:
- Education, skills, certifications, and experience are grouped into groups.
- Each group has:
  - group_id (e.g., "edu1", "skill1", "cert1", "exp1")
  - operator: "AND", "OR", "N_OF"
  - min_required: only for N_OF, otherwise null
  - mandatory: true if required, false if preferred/optional
- For education:
  - degrees: list of DegreeRequirement (degree: "Bachelor's", "Master's", etc., fields: list of fields)
- For skills:
  - skills: list of SkillRequirement (skill_name, category, min_experience_years, proficiency_level, weight)
- For certifications:
  - certifications: list of CertificationRequirement (certification_name, issuing_body)
- For experience:
  - experiences: list of ExperienceRequirement (experience_area, min_years, max_years)
For soft skills:
- Output ONLY a list of strings
- Do NOT output objects
- Do NOT include proficiency, weight, or experience

Job Description:
{job_text}
"""

def create_metadata_prompt(global_context: str) -> str:
    """Return the prompt for extracting job metadata."""
    return f"""
{global_context}

Task:
Extract job metadata from the job description. Output as JSON with:
- job_title
- industry
- employment_type
- work_mode
- location (city, state, country)
- experience_required_years (min, max)
- posted_date (if available, else null)
- responsibilities (list of strings)
- salary (min_amount, max_amount, currency, period, raw_text)

Output only the JSON object.
"""

def create_group_prompt(global_context: str, requirement_type: str, prefix: str, items_key: str) -> str:
    """Return a generic group prompt for education, skills, certifications, experience."""
    return f"""
{global_context}

Task:
Extract and structure {requirement_type} requirements from the job description into a structured group format.

Rules:
- Group related items logically.
- Use:
  - "AND" if all items in the group must be satisfied.
  - "OR" if any one item in the group is sufficient.
  - "N_OF" if a minimum number of items must be satisfied (use min_required).
- Set "mandatory": true if the requirement is explicitly required (e.g., "must have", "required").
- Set "mandatory": false if the requirement is preferred, optional, or a "plus".
- Use clear, normalized names (e.g., "Bachelor's", "Python", "AWS Certification", "AI/ML").
- Output only a JSON list of groups, each with:
  - group_id (e.g., "{prefix}1")
  - operator ("AND", "OR", "N_OF")
  - min_required (only for N_OF, otherwise null)
  - mandatory (true/false)
  - {items_key}

Output only the JSON list.
"""

def create_assembly_prompt(
    global_context: str,
    metadata: dict,
    education_groups: list,
    skill_groups: list,
    certification_groups: list,
    experience_groups: list,
    responsibilities: list,
    salary: dict
) -> str:
    """Return the prompt for assembling the final JSON."""
    return f"""
{global_context}

Task:
Given:
- job_metadata: {metadata}
- education_groups: {education_groups}
- skill_groups: {skill_groups}
- certification_groups: {certification_groups}
- experience_groups: {experience_groups}
- responsibilities: {responsibilities}
- salary: {salary}

Assemble them into a single JSON object matching this schema:
{{
  "job_metadata": {{ ... }},
  "education_requirements": {{ "groups": [...] }},
  "skill_requirements": {{ "groups": [...] }},
  "certification_requirements": {{ "groups": [...] }},
  "experience_requirements": {{ "groups": [...] }},
  "soft_skill_requirements": {{ "skills": [...] }},
  "responsibilities": [...],
  "salary": {{ ... }}
}}

Output only the final JSON.
"""
