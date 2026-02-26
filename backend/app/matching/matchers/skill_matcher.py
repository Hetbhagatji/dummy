from app.services.normalization.object import TextNormalizer
from app.schemas.job_schema import Job
from app.schemas.resume_schema.resume_schema import Resume
from typing import List,Dict
from app.embedding_models.embedder import ResumeJobEmbedder
from app.raw_extractors.skill_extractor import evaluate_skill_group,extract_job_skills,extract_resume_skills
class SkillMatcher:
    def __init__(self, embedder: ResumeJobEmbedder, similarity_threshold: float = 0.6):
        self.embedder = embedder
        self.SIMILARITY_THRESHOLD = similarity_threshold
    def match_skills(self, resume: Resume, job: Job) -> Dict:
        """Main skill matching with group logic - NO PENALTY
        
        Returns:
            {
                "score": float,
                "matched_skills": List[str],  # ✅ NEW!
                "total_required": int
            }
        """
        resume_skills = extract_resume_skills(resume)
        
        if not job.skill_requirements or not job.skill_requirements.groups:
            return {"score": 0.0, "matched_skills": [], "total_required": 0}
        
        if not resume_skills:
            return {"score": 0.0, "matched_skills": [], "total_required": 0}

        group_results = []
        matched_skills_set = set()  # ✅ Track matched skills
        total_required = 0

        for group in job.skill_requirements.groups:
            result = evaluate_skill_group(group, resume_skills, self.SIMILARITY_THRESHOLD)
            group_results.append(result)
            
            # ✅ Track which skills matched
            matched_skills_set.update(result.get("matched_skill_names", []))
            total_required += result["required_count"]

        if not group_results:
            return {"score": 0.0, "matched_skills": [], "total_required": 0}

        avg_score = sum(g["group_score"] for g in group_results) / len(group_results)

        return {
            "score": float(round(avg_score, 3)),
            "matched_skills": list(matched_skills_set),  # ✅ Return matched skills
            "total_required": total_required
        }
