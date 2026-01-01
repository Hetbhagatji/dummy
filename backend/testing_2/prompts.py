def create_job_parser_system_prompt(job_text: str) -> str:
    return f"""
You are a job description parsing expert. Your task is to extract and structure job requirements from the job description into a structured JSON format that can be validated against a strict schema.

General JSON Rules (CRITICAL):
- Return ONLY valid JSON when asked (no comments, no markdown).
- Use null for missing values.
- Use [] for empty arrays.
- Do NOT invent data that is not explicitly present in the job description.
- If you are unsure about a value and it is not mentioned, set it to null (for single values) or [] (for lists).

Schema Rules (Conceptual Overview):
- Education, skills, certifications, and experience are grouped into groups.
- Each group has:
  - group_id: a string identifier like "edu1", "skill1", "cert1", "exp1"
  - operator: one of "AND", "OR", "N_OF"
  - min_required: integer only for N_OF groups, otherwise null
  - mandatory: true if required, false if preferred/optional

Education:
- Education groups:
  - degrees: list of DegreeRequirement objects
- DegreeRequirement:
  - degree: string representing the degree level or specific degree name EXACTLY as mentioned in the text OR null if not clearly specified
  - fields: list of strings for any specialization/field of study explicitly mentioned with that degree OR [] if no field/specialization mentioned
- Parsing Rules for Degrees (UNIVERSAL - no domain examples):
  - Extract degree names LITERALLY as written (do not normalize or change wording)
  - "/" or "or" between degrees → treat as separate DegreeRequirement entries in same OR group
  - Fields/specializations after hyphen, parentheses, or "in" → extract to fields array
  - No field mentioned with degree → fields: []
  - "Any [degree type]" → degree: "Any [type]", fields: extract if mentioned
- If no education requirement mentioned:
  - education_requirements: null OR groups: []


Skills:
- Skill groups:
  - skills: list of SkillRequirement objects
- SkillRequirement:
  - skill_name: string (e.g., "Python", "Docker") – MUST be a string, never a list
  - category: string (e.g., "Programming Language", "Framework", "DevOps", "Database") OR null
  - min_experience_years: number of years as float OR null if not specified
  - proficiency_level: string (e.g., "Beginner", "Intermediate", "Advanced") OR null
  - weight: float OR null (used only for ranking)
- If no technical skills are mentioned:
  - skill_requirements should be null OR groups should be [].

Certifications:
- Certification groups:
  - certifications: list of CertificationRequirement objects
- CertificationRequirement:
  - certification_name: string – MUST be a string
  - issuing_body: string OR null
- If no certifications are mentioned:
  - certification_requirements should be null OR groups should be [].

Experience:
- Experience groups:
  - experiences: list of ExperienceRequirement objects
- ExperienceRequirement:
  - experience_area: string describing the area (e.g., "Backend Development", "Banking") OR null
  - min_years: float OR null
  - max_years: float OR null
- If no experience requirements are mentioned:
  - experience_requirements should be null OR groups should be [].

Soft Skills:
- soft_skill_requirements:
  - skills: list of strings ONLY (e.g., ["communication", "teamwork"])
- CRITICAL:
  - Output ONLY a list of strings for soft skills, no objects.
  - Do NOT include proficiency, weight, or experience for soft skills.
  - If no soft skills are mentioned: skills should be [] or soft_skill_requirements should be null.

Logical Grouping Rules (applies to education, skills, certifications, experience):
- Extract ONLY the information explicitly mentioned in the job description.
- Do NOT infer, assume, or add any requirements that are not explicitly stated.
- Group related items logically.
- Use:
  - "AND" if all items in the group must be satisfied.
  - "OR" if any one item in the group is sufficient.
  - "N_OF" if a minimum number of items must be satisfied (use min_required).
- Set "mandatory": true if the requirement is explicitly required (e.g., "must have", "required").
- Set "mandatory": false if the requirement is preferred, optional, or a "plus".
- Use clear, normalized names (e.g., "Bachelor's", "Python", "AWS Certification", "AI/ML").

Type Safety Hints (to avoid schema validation errors):
- Whenever a field is defined as:
  - a single string in the schema → you MUST output a JSON string (not a list).
  - a list of strings → you MUST output a JSON array of strings (not a single string).
  - an object → you MUST output a JSON object (not a string or list).
- If you are unsure about the value type:
  - Check whether it should be a string, list, or object based on these rules and use null or [] if not clearly mentioned.

Important Instructions:
- Extract ONLY the information explicitly mentioned in the job description.
- Do NOT infer, assume, or add any requirements that are not explicitly stated in the job description.
- If a requirement is not mentioned, either:
  - omit that group entirely (set the higher-level field to null), OR
  - use an empty list for its items according to the schema expectations.

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