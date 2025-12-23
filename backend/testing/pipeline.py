from prompts import create_assembly_prompt,create_group_prompt,create_job_parser_system_prompt,create_metadata_prompt
from groqq import call_groq
import json
def parse_job_description(job_text: str) -> dict:
    """Parse a job description into the Job schema using Groq API."""
    
    # Step 1: Create global context
    global_context = create_job_parser_system_prompt(job_text)
    
    # Step 2: Extract metadata
    metadata_prompt = create_metadata_prompt(global_context)
    metadata_json = call_groq(metadata_prompt)
    metadata = json.loads(metadata_json)
    
    # Step 3: Parse education
    education_prompt = create_group_prompt(global_context, "education", "edu", "degrees")
    education_groups_json = call_groq(education_prompt)
    education_groups = json.loads(education_groups_json)
    
    # Step 4: Parse skills
    skills_prompt = create_group_prompt(global_context, "skills", "skill", "skills")
    skill_groups_json = call_groq(skills_prompt)
    skill_groups = json.loads(skill_groups_json)
    
    # Step 5: Parse certifications
    certifications_prompt = create_group_prompt(global_context, "certifications", "cert", "certifications")
    certification_groups_json = call_groq(certifications_prompt)
    certification_groups = json.loads(certification_groups_json)
    
    # Step 6: Parse experience
    experience_prompt = create_group_prompt(global_context, "experience", "exp", "experiences")
    experience_groups_json = call_groq(experience_prompt)
    experience_groups = json.loads(experience_groups_json)
    
    # Step 7: Extract responsibilities and salary (if not in metadata)
    responsibilities = metadata.get("responsibilities", [])
    salary = metadata.get("salary", None)
    
    # Step 8: Assemble final JSON
    assembly_prompt = create_assembly_prompt(
        global_context,
        metadata,
        education_groups,
        skill_groups,
        certification_groups,
        experience_groups,
        responsibilities,
        salary
    )
    final_json = call_groq(assembly_prompt)
    
    return json.loads(final_json)
