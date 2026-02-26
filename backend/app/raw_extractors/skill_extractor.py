from app.services.normalization.object import TextNormalizer
from typing import List
from app.schemas.resume_schema.resume_schema import Resume
from app.embedding_models.embedder import ResumeJobEmbedder
embedder = ResumeJobEmbedder()

def extract_job_skills( job_skill_requirements) -> List[str]:
    """Extract all job skills for display"""
    if not job_skill_requirements or not job_skill_requirements.groups:
        return []
    
    job_skills = []
    for group in job_skill_requirements.groups:
        for skill in group.skills:
            job_skills.append(TextNormalizer.normalize(skill.skill_name))
    return job_skills

def extract_resume_skills(resume: Resume) -> List[str]:
    """Extract normalized skill names from resume skills and work experience"""
    skill_set = set()
    
    # Extract from Skills section
    if resume.skills and resume.skills.skills:
        for s in resume.skills.skills:
            skill_set.add(TextNormalizer.normalize(s.skill_name))
    
    # Extract from each WorkExperience's skills
    if resume.experience and resume.experience.experience_areas:
        for work_exp in resume.experience.experience_areas:
            if work_exp.skills:
                for s in work_exp.skills:
                    skill_set.add(TextNormalizer.normalize(s.skill_name))
    
    return list(skill_set)

def match_single_skill(job_skill: str, resume_skills: List[str], threshold: float) -> float:
    """Returns best similarity score for a job skill against all resume skills"""
    if not resume_skills:
        return 0.0

    job_vec = embedder.embed_texts([job_skill])[0]
    resume_vecs = embedder.embed_texts(resume_skills)

    similarities = [
        embedder.cosine_similarity(job_vec, r_vec)
        for r_vec in resume_vecs
    ]

    best_score = max(similarities)
    return best_score if best_score >= threshold else 0.0

def evaluate_skill_group( group, resume_skills: List[str], threshold: float) -> dict:
    skill_scores = []
    matched_skill_names = []  # ✅ NEW!

    for skill in group.skills:
        skill_name = TextNormalizer.normalize(skill.skill_name)
        score = match_single_skill(
            skill_name,
            resume_skills,
            threshold
        )
        skill_scores.append(score)
        
        # ✅ Track which skills matched
        if score > 0:
            matched_skill_names.append(skill_name)

    matched = sum(1 for s in skill_scores if s > 0)
    total = len(skill_scores)
    # Operator Logic
    if group.operator == "AND":
        base_score = sum(skill_scores) / total if total else 0.0
        coverage = matched / total if total else 0.0
        group_score = base_score
        passed = matched == total

    elif group.operator == "OR":
        if not skill_scores:
            group_score = 0.0
        else:
            best_score = max(skill_scores)
            coverage = matched / total if total else 0.0
            # 70% from best match + 30% bonus for breadth
            group_score = (best_score * 0.7) + (coverage * 0.3)
        passed = matched >= 1

    elif group.operator == "N_OF":
        min_req = group.min_required or 1
        # Base score from average
        base_score = sum(skill_scores) / total if total else 0.0
        # Bonus if exceeding minimum
        if matched >= min_req:
            # Give full credit plus small bonus for extras
            coverage = matched / total if total else 0.0
            group_score = (base_score * 0.8) + (coverage * 0.2)
        else:
            # Partial credit if below minimum
            group_score = base_score * (matched / min_req)
        passed = matched >= min_req

    else:
        group_score = sum(skill_scores) / total if total else 0.0
        passed = matched >= 1

    if group.min_required is not None:
        passed = matched >= group.min_required

    return {
        "group_score": float(round(group_score, 3)),
        "matched_count": matched,
        "required_count": total,
        "passed": passed,
        "mandatory": group.mandatory,
        "matched_skill_names": matched_skill_names  # ✅ NEW!
    }