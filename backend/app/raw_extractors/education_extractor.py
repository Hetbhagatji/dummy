from typing import List
from app.schemas.job_schema import EducationRequirements
from app.schemas.resume_schema.education_schema import Education
from app.services.normalization.object import TextNormalizer
from app.embedding_models.embedder import ResumeJobEmbedder

embedder = ResumeJobEmbedder()
DEGREE_LEVEL_RANK = {
    "diploma": 1,
    "associate": 2,
    "bachelor's": 3,
    "bachelor": 3,
    "master": 4,
    "master's": 4,
    "phd": 5,
    "doctorate": 5
}



def extract_resume_education(resume_education: Education) -> List[str]:
    """Extract resume education for display"""
    if not resume_education or not resume_education.entries:
        return []
    
    education_list = []
    for entry in resume_education.entries:
        level = entry.degree_level or "Unspecified Level"
        fields = ", ".join(entry.field) if entry.field else "No Fields"
        education_list.append(f"{level}: {fields}")
    return education_list

def extract_job_education(job_education: EducationRequirements) -> List[str]:
    """Extract job education requirements for display"""
    if not job_education or not job_education.groups:
        return []
    
    education_list = []
    for group in job_education.groups:
        for degree_req in group.degrees:
            level = degree_req.degree_level or "Unspecified Level"
            fields = ", ".join(degree_req.fields) if degree_req.fields else "No Fields"
            education_list.append(f"{level}: {fields}")
    return education_list

def extract_resume_degree_combinations(resume_education) -> List[tuple]:
    """Extract degree combinations as (level, field) pairs"""
    if not resume_education or not resume_education.entries:
        return []
    
    combinations = []
    for entry in resume_education.entries:
        level = normalize_level(entry.degree_level)
        if entry.field:
            for field in entry.field:
                cleaned_field = TextNormalizer.normalize(field.strip())
                if cleaned_field and level:
                    # Store as tuple: (level, field)
                    combinations.append((level, cleaned_field))
    return combinations

def normalize_level(level: str) -> str:
    """Normalize degree level string"""
    if not level:
        return ""
    return level.strip().lower()

def extract_resume_levels( resume_education) -> List[int]:
    """Extract degree level ranks from resume"""
    if not resume_education or not resume_education.entries:
        return []
    
    levels = []
    for entry in resume_education.entries:
        level = normalize_level(entry.degree_level)
        if level in DEGREE_LEVEL_RANK:
            levels.append(DEGREE_LEVEL_RANK[level])
    return levels

def extract_job_levels(job_education) -> List[int]:
    """Extract degree level ranks from job requirements"""
    if not job_education or not job_education.groups:
        return []
    
    levels = []
    for group in job_education.groups:
        for degree in group.degrees:
            level = normalize_level(degree.degree_level)
            if level in DEGREE_LEVEL_RANK:
                levels.append(DEGREE_LEVEL_RANK[level])
    return levels

def check_level_capability(resume_levels: List[int], job_levels: List[int]) -> bool:
    """
    FIRST CHECK: Does candidate meet minimum level requirement?
    """
    if not resume_levels or not job_levels:
        return False
    
    highest_resume_level = max(resume_levels)
    return any(highest_resume_level >= required_level for required_level in job_levels)


def match_single_degree_combination(job_level: str, job_field: str, 
                                    resume_combinations: List[tuple], 
                                    threshold: float) -> float:
    """Match a job requirement (level+field) against resume degree combinations"""
    if not resume_combinations:
        return 0.0
    
    # Create combined string for job requirement
    job_combined = f"{job_level} in {job_field}"
    job_vec = embedder.embed_texts([job_combined])[0]
    
    # Create combined strings for all resume combinations
    resume_combined_texts = [
        f"{level} in {field}" for level, field in resume_combinations
    ]
    resume_vecs = embedder.embed_texts(resume_combined_texts)
    
    # Find best match
    similarities = [
        embedder.cosine_similarity(job_vec, r_vec)
        for r_vec in resume_vecs
    ]
    
    best_score = max(similarities)
    return best_score if best_score >= threshold else 0.0

def evaluate_education_group(group, resume_combinations: List[tuple]) -> dict:
    """Evaluate SINGLE group with AND/OR/N_OF logic"""
    degree_scores = []
    
    for degree_req in group.degrees:
        level = normalize_level(degree_req.degree_level)
        field_scores = []
        
        for job_field in degree_req.fields:
            normalized_job_field = TextNormalizer.normalize(job_field)
            # Match complete degree combination
            best_score = match_single_degree_combination(
                level, normalized_job_field, resume_combinations, 
                # self.FIELD_SIMILARITY_THRESHOLD
                0.7
            )
            field_scores.append(best_score)
        
        degree_score = sum(field_scores) / len(field_scores) if field_scores else 0.0
        degree_scores.append(degree_score)
    
    matched = sum(1 for s in degree_scores if s >= 0.7)
    total = len(degree_scores)

    # ========== OPERATOR LOGIC (unchanged) ==========
    if group.operator == "AND":
        base_score = sum(degree_scores) / total if total else 0.0
        coverage = matched / total if total else 0.0
        group_score = base_score 
        passed = matched == total

    elif group.operator == "OR":
        if not degree_scores:
            group_score = 0.0
        else:
            best_score = max(degree_scores)
            coverage = matched / total if total else 0.0
            group_score = (best_score * 0.7) + (coverage * 0.3)
        passed = matched >= 1

    elif group.operator == "N_OF":
        min_req = group.min_required or 1
        base_score = sum(degree_scores) / total if total else 0.0
        if matched >= min_req:
            coverage = matched / total if total else 0.0
            group_score = (base_score * 0.8) + (coverage * 0.2)
        else:
            group_score = base_score * (matched / min_req)
        passed = matched >= min_req

    else:
        group_score = max(degree_scores) if degree_scores else 0.0
        passed = matched >= 1
    
    if group.min_required is not None:
        passed = matched >= group.min_required
    
    return {
        "group_score": float(round(group_score, 3)),
        "matched_count": matched,
        "required_count": total,
        "passed": passed,
        "mandatory": group.mandatory
    }