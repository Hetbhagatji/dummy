def create_job_parser_system_prompt(job_text: str) -> str:
    return f"""
You are a job description parsing expert. Your task is to extract and structure job requirements into a structured format, including nested logical groups for any industry.


Schema Rules:
- Only extract information that is explicitly present in the job description. Do not infer or hallucinate information.
- If no requirement is explicitly mentioned for education, certifications, experience, or soft skills, output the corresponding field as null or an empty list.
- Group requirements for education, skills, certifications, and experience.
- Each group must have:
  - group_id (e.g., "edu1", "skill1", "cert1", "exp1")
  - operator: "AND", "OR", "N_OF"
  - min_required: only for "N_OF", otherwise null
  - mandatory: true if required, false if preferred/optional
- For education:
  - degrees: list of DegreeRequirement (degree: "Bachelor's", "Master's", etc., fields: list of fields)
  - If no education requirement is explicitly mentioned, output "education_requirements": {{"groups": []}}
- For skills:
  - skills: list of SkillRequirement (skill_name, category, min_experience_years, proficiency_level, weight)
- For certifications:
  - certifications: list of CertificationRequirement (certification_name, issuing_body)
  - If no certification is explicitly mentioned, output "certification_requirements": {{"groups": []}}
- For experience:
  - experiences: list of ExperienceRequirement (experience_area, min_years, max_years)
  - If no specific experience area is explicitly mentioned, output "experience_requirements": {{"groups": []}}
- For soft skills:
  - Output ONLY a list of strings
  - Do NOT output objects
  - Do NOT include proficiency, weight, or experience
  - If no soft skills are explicitly mentioned, output "soft_skill_requirements": {{"skills": []}}
- For responsibilities:
  - If no responsibilities are explicitly mentioned, output "responsibilities": []


Logical Grouping Rules:
- Group related items logically, regardless of industry.
- Use:
  - "AND" if all items in the group must be satisfied.
  - "OR" if any one item in the group is sufficient.
  - "N_OF" if a minimum number of items must be satisfied (use min_required).
- Nest groups if requirements are complex (e.g., "X AND (Y OR Z)").
- Set "mandatory": true for required skills, experience, or education; false for preferred/optional.
- Normalize names (e.g., "Bachelor's", "Python", "AWS Certification", "AI/ML", "Sales", "Communication").
- Handle edge cases:
  - If a requirement is ambiguous, prefer a broader group.
  - If a requirement is nested (e.g., "must have X AND (Y OR Z)"), create nested groups.
  - If a requirement is optional, set "mandatory": false.
  - If a requirement is missing, leave it null.


Context and Similarity Instructions:
- Identify the context of each requirement (e.g., backend development, data analysis).
- Use semantic similarity to group items that are contextually related but may not be in the same category.
- For example, if the requirement mentions a specific role (e.g., "backend development"), use the role to guide the grouping.
- If all items in the list are of the same type (e.g., all frameworks or all databases), group them under a single "OR" group.
- If there’s a mix of types (e.g., a language and frameworks), create a nested "AND" group with the language and an inner "OR" group for the frameworks.


Experience Requirements:
- Only extract experience requirements that are explicitly mentioned in the job description.
- Do not infer or generalize experience requirements.
- For example, if the job description mentions "Azure DevOps" and "Cloud Architecture", only extract those.
- If the job description only mentions "Azure platforms", do not split into "Azure DevOps" and "Cloud Architecture" unless explicitly stated.


Example:
- "A AND (B OR C)" should be:
  {{
    "group_id": "skill1",
    "operator": "AND",
    "min_required": null,
    "mandatory": true,
    "skills": [{{"skill_name": "A", "category": ""}}],
    "groups": [
      {{
        "group_id": "skill2",
        "operator": "OR",
        "min_required": null,
        "mandatory": true,
        "skills": [
          {{"skill_name": "B", "category": ""}},
          {{"skill_name": "C", "category": "Framework"}}
        ],
        "groups": []
      }}
    ]
  }}


Job Description:
{job_text}
"""



def create_metadata_prompt(global_context: str) -> str:
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
    return f"""
{global_context}


Task:
Extract and structure {requirement_type} requirements from the job description into a structured group format.

Rules:
- Group related items logically, regardless of industry.
- Use:
  - "AND" if all items in the group must be satisfied.
  - "OR" if any one item in the group is sufficient.
  - "N_OF" if a minimum number of items must be satisfied (use min_required).
- Set "mandatory": true if the requirement is explicitly required (e.g., "must have", "required").
- Set "mandatory": false if the requirement is preferred, optional, or a "plus".
- Use clear, normalized names (e.g., "Bachelor's", "Python", "AWS Certification", "AI/ML", "Sales", "Communication").
- Only extract requirements that are explicitly mentioned in the job description.
- Do not infer or generalize requirements.
- Output only a JSON list of groups, each with:
  - group_id (e.g., "{prefix}1")
  - operator ("AND", "OR", "N_OF")
  - min_required (only for N_OF, otherwise null)
  - mandatory (true/false)
  - {items_key}

Context and Similarity Instructions:
- Identify the context of each requirement.
- Use semantic similarity to group items that are contextually related.
- If all items are of the same type, group them under a single "OR" group.
- If there’s a mix of types, create a nested "AND" group with an inner "OR" group for the frameworks.

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
