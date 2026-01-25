from app.embedding_models.embedder import ResumeJobEmbedder
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.job_schema import Job, ExperienceRequirements
from typing import Dict, List
from app.schemas.matching_preferences import MatchingPreferences
import numpy as np
from app.services.normalization.object import normalize_object
from app.services.normalization.text import TextNormalizer
from app.schemas.resume_schema.education_schema import Education
from app.schemas.job_schema import EducationRequirements
from app.schemas.resume_schema.certifications_schema import Certifications
from app.schemas.job_schema import CertificationRequirements
from app.schemas.resume_schema.experience_schema import Experience
from app.schemas.resume_schema.skills_schema import Skills


DEGREE_LEVEL_RANK = {
    "diploma": 1,
    "associate": 2,
    "bachelor's": 3,
    "bachelor": 3,  # Fixed: was duplicate "bachelor's"
    "master": 4,
    "master's": 4,
    "phd": 5,
    "doctorate": 5
}


class SimilarityMatcher:
    def __init__(self):
        self.embedder = ResumeJobEmbedder()
        self.SIMILARITY_THRESHOLD = 0.7
        self.FIELD_SIMILARITY_THRESHOLD = 0.65  # Moved inside class
    
    # ==================== SKILL MATCHING ====================
    
    def extract_resume_skills(self, resume_skills: Skills) -> List[str]:
        """Extract normalized skill names from resume"""
        if not resume_skills or not resume_skills.skills:
            return []
        return [TextNormalizer.normalize(s.skill_name) for s in resume_skills.skills]
    
    def match_single_skill(self, job_skill: str, resume_skills: List[str], threshold: float) -> float:
        """Returns best similarity score for a job skill against all resume skills"""
        if not resume_skills:
            return 0.0

        job_vec = self.embedder.embed_texts([job_skill])[0]
        resume_vecs = self.embedder.embed_texts(resume_skills)

        similarities = [
            self.embedder.cosine_similarity(job_vec, r_vec)
            for r_vec in resume_vecs
        ]

        best_score = max(similarities)
        return best_score if best_score >= threshold else 0.0

    def evaluate_skill_group(self, group, resume_skills: List[str], threshold: float) -> dict:
        """
        Evaluate a skill group with AND/OR/N_OF logic
        Returns: {group_score, matched_count, required_count, passed, mandatory}
        """
        skill_scores = []

        for skill in group.skills:
            score = self.match_single_skill(
                TextNormalizer.normalize(skill.skill_name),
                resume_skills,
                threshold
            )
            skill_scores.append(score)

        matched = sum(1 for s in skill_scores if s > 0)
        total = len(skill_scores)

        # Operator Logic
        if group.operator == "AND":
            # All skills must match
            base_score = sum(skill_scores) / total if total else 0.0
            coverage = matched / total if total else 0.0
            group_score = base_score * coverage
            passed = matched == total

        elif group.operator == "OR":
            # At least one skill must match
            group_score = max(skill_scores) if skill_scores else 0.0
            passed = matched >= 1

        elif group.operator == "N_OF":
            # At least N skills must match (specified by min_required)
            group_score = sum(skill_scores) / total if total else 0.0
            passed = matched >= (group.min_required or 1)

        else:
            # Fallback
            group_score = sum(skill_scores) / total if total else 0.0
            passed = matched >= 1

        # Min required override
        if group.min_required is not None:
            passed = matched >= group.min_required

        return {
            "group_score": round(group_score, 3),
            "matched_count": matched,
            "required_count": total,
            "passed": passed,
            "mandatory": group.mandatory
        }
    
    def match_skills(self, resume: Resume, job: Job) -> float:
        """Main skill matching with group logic"""
        resume_skills = self.extract_resume_skills(resume.skills)
        
        if not job.skill_requirements or not job.skill_requirements.groups:
            return 0.0
        
        if not resume_skills:
            return 0.0

        group_results = []
        penalty = 1.0

        for group in job.skill_requirements.groups:
            result = self.evaluate_skill_group(group, resume_skills, self.SIMILARITY_THRESHOLD)
            group_results.append(result)

            # Mandatory group penalty
            if result["mandatory"] and not result["passed"]:
                penalty *= 0.6

        if not group_results:
            return 0.0

        avg_score = sum(g["group_score"] for g in group_results) / len(group_results)
        final_score = avg_score * penalty

        return float(round(final_score, 3))
    
    def extract_job_skills(self, job_skill_requirements) -> List[str]:
        """Extract all job skills for display"""
        if not job_skill_requirements or not job_skill_requirements.groups:
            return []
        
        job_skills = []
        for group in job_skill_requirements.groups:
            for skill in group.skills:
                job_skills.append(TextNormalizer.normalize(skill.skill_name))
        return job_skills
    
   # ==================== EDUCATION MATCHING ====================
    
    def normalize_level(self, level: str) -> str:
        """Normalize degree level string"""
        if not level:
            return ""
        return level.strip().lower()
    
    def extract_resume_levels(self, resume_education) -> List[int]:
        """Extract degree level ranks from resume"""
        if not resume_education or not resume_education.entries:
            return []
        
        levels = []
        for entry in resume_education.entries:
            level = self.normalize_level(entry.degree_level)
            if level in DEGREE_LEVEL_RANK:
                levels.append(DEGREE_LEVEL_RANK[level])
        return levels

    def extract_job_levels(self, job_education) -> List[int]:
        """Extract degree level ranks from job requirements"""
        if not job_education or not job_education.groups:
            return []
        
        levels = []
        for group in job_education.groups:
            for degree in group.degrees:
                level = self.normalize_level(degree.degree_level)
                if level in DEGREE_LEVEL_RANK:
                    levels.append(DEGREE_LEVEL_RANK[level])
        return levels
    
    def check_level_capability(self, resume_levels: List[int], job_levels: List[int]) -> bool:
        """
        FIRST CHECK: Does candidate meet minimum level requirement?
        Candidate must have AT LEAST ONE degree that meets ANY job required level
        """
        if not resume_levels or not job_levels:
            return False
        
        highest_resume_level = max(resume_levels)
        # Candidate is capable if their highest level >= ANY required job level
        return any(highest_resume_level >= required_level for required_level in job_levels)
    
    def extract_resume_fields_only(self, resume_education) -> List[str]:
        """Extract ONLY individual fields from resume (no degree_name)"""
        if not resume_education or not resume_education.entries:
            return []
        
        fields = []
        for entry in resume_education.entries:
            if entry.field:  # entry.field is list of field names
                for field in entry.field:
                    cleaned_field = TextNormalizer.normalize(field.strip())
                    if cleaned_field:
                        fields.append(cleaned_field)
        return fields
    
    def extract_job_fields_only(self, job_education) -> List[str]:
        """Extract ONLY individual fields from job requirements (no degree_name)"""
        if not job_education or not job_education.groups:
            return []
        
        fields = []
        for group in job_education.groups:
            for degree_req in group.degrees:
                if degree_req.fields:  # degree_req.fields is list of field names
                    for field in degree_req.fields:
                        cleaned_field = TextNormalizer.normalize(field.strip())
                        if cleaned_field:
                            fields.append(cleaned_field)
        return fields
    
    def match_fields_individual(self, job_fields: List[str], resume_fields: List[str]) -> dict:
        """
        Match INDIVIDUAL fields separately using embeddings
        Returns field-level matching details
        """
        if not job_fields or not resume_fields:
            return {"matched": False, "field_scores": [], "matched_count": 0, "total_job_fields": 0}
        
        job_embeddings = self.embedder.embed_texts(job_fields)
        resume_embeddings = self.embedder.embed_texts(resume_fields)
        
        field_scores = []
        matched_count = 0
        
        for i, job_field in enumerate(job_fields):
            best_score = 0.0
            best_match = None
            
            for j, resume_field in enumerate(resume_fields):
                score = self.embedder.cosine_similarity(job_embeddings[i], resume_embeddings[j])
                if score > best_score:
                    best_score = score
                    best_match = resume_field
            
            field_scores.append({
                "job_field": job_field,
                "best_resume_match": best_match,
                "score": float(best_score)
            })
            
            if best_score >= self.FIELD_SIMILARITY_THRESHOLD:
                matched_count += 1
        
        total_job_fields = len(job_fields)
        overall_matched = matched_count >= 1  # At least one field match
        
        return {
            "matched": overall_matched,
            "field_scores": field_scores,
            "matched_count": matched_count,
            "total_job_fields": total_job_fields,
            "match_percentage": matched_count / total_job_fields if total_job_fields > 0 else 0.0
        }
    
    def match_education(self, resume_education: Education, job_education: EducationRequirements) -> float:
        """Main education matching: LEVEL FIRST, then INDIVIDUAL FIELDS"""
        if not resume_education or not resume_education.entries:
            return 0.0
        
        if not job_education or not job_education.groups:
            return 0.0
        
        # STEP 1: LEVEL CHECK - Candidate must be capable first
        resume_levels = self.extract_resume_levels(resume_education)
        job_levels = self.extract_job_levels(job_education)
        
        if not self.check_level_capability(resume_levels, job_levels):
            return 0.0  # Candidate doesn't meet minimum level requirement
        
        # STEP 2: Extract individual fields only (no degree_name)
        resume_fields = self.extract_resume_fields_only(resume_education)
        job_fields = self.extract_job_fields_only(job_education)
        
        if not resume_fields or not job_fields:
            return 0.0
        
        # STEP 3: Match individual fields separately
        field_match = self.match_fields_individual(job_fields, resume_fields)
        
        # Calculate final score based on field matching percentage
        field_score = field_match["match_percentage"]
        
        # Bonus for perfect field matches or high coverage
        if field_match["matched_count"] == field_match["total_job_fields"]:
            field_score *= 1.2  # Perfect field match bonus
        
        return float(round(min(field_score, 1.0), 3))
    
    def extract_resume_education(self, resume_education: Education) -> List[str]:
        """Extract resume education for display (fields only, no degree_name)"""
        if not resume_education or not resume_education.entries:
            return []
        
        education_list = []
        for entry in resume_education.entries:
            level = entry.degree_level or "Unspecified Level"
            fields = ", ".join(entry.field) if entry.field else "No Fields"
            education_list.append(f"{level}: {fields}")
        return education_list
    
    def extract_job_education(self, job_education: EducationRequirements) -> List[str]:
        """Extract job education requirements for display (fields only, no degree_name)"""
        if not job_education or not job_education.groups:
            return []
        
        education_list = []
        for group in job_education.groups:
            for degree_req in group.degrees:
                level = degree_req.degree_level or "Unspecified Level"
                fields = ", ".join(degree_req.fields) if degree_req.fields else "No Fields"
                education_list.append(f"{level}: {fields}")
        return education_list

    # ==================== OTHER MATCHING METHODS ====================
    # [Keep all other methods unchanged - certifications, experience, skills, etc.]
    
    def match_single_skill(self, job_skill: str, resume_skills: List[str], threshold: float) -> float:
        """Returns best similarity score for a job skill against all resume skills"""
        if not resume_skills:
            return 0.0
        job_vec = self.embedder.embed_texts([job_skill])[0]
        resume_vecs = self.embedder.embed_texts(resume_skills)
        similarities = [self.embedder.cosine_similarity(job_vec, r_vec) for r_vec in resume_vecs]
        best_score = max(similarities)
        return best_score if best_score >= threshold else 0.0

    def extract_resume_skills(self, resume_skills: Skills) -> List[str]:
        """Extract normalized skill names from resume"""
        if not resume_skills or not resume_skills.skills:
            return []
        return [TextNormalizer.normalize(s.skill_name) for s in resume_skills.skills]

    def match_skills(self, resume: Resume, job: Job) -> float:
        """Main skill matching with group logic"""
        resume_skills = self.extract_resume_skills(resume.skills)
        if not job.skill_requirements or not job.skill_requirements.groups:
            return 0.0
        if not resume_skills:
            return 0.0
        # Simplified skill matching - implement full group logic as before
        return 0.85  # Placeholder

    # ... [Include other methods as needed]

    def compute_final_score(self, resume: Resume, job: Job, prefs: MatchingPreferences = None) -> Dict:
        """Compute final matching score with detailed breakdown"""
        resume = normalize_object(resume)
        job = normalize_object(job)
        
        if prefs is None:
            prefs = MatchingPreferences()
        
        # Calculate individual scores
        scores = {
            "skills": self.match_skills(resume, job),
            "experience": self.match_experience_years(job.experience_requirements, resume.experience) if hasattr(self, 'match_experience_years') else 0.0,
            "education": self.match_education(resume.education, job.education_requirements),
            "certifications": self.match_certifications(resume.certifications, job.certification_requirements) if hasattr(self, 'match_certifications') else 0.0,
            "responsibilities": self.match_responsibilities(resume.experience, job) if hasattr(self, 'match_responsibilities') else 0.0
        }
        
        final = (
            scores["skills"] * getattr(prefs, 'skill_match_weight', 0.25) +
            scores["experience"] * getattr(prefs, 'experience_match_weight', 0.25) +
            scores["education"] * getattr(prefs, 'education_match_weight', 0.20) +
            scores["certifications"] * getattr(prefs, 'certification_match_weight', 0.15) +
            scores["responsibilities"] * getattr(prefs, 'responsibilities_match_weight', 0.15)
        )
        
        return {
            "scores": scores,
            "education_details": {
                "resume_education": self.extract_resume_education(resume.education),
                "job_education": self.extract_job_education(job.education_requirements),
                "level_capable": self.check_level_capability(
                    self.extract_resume_levels(resume.education),
                    self.extract_job_levels(job.education_requirements)
                )
            },
            "final_match": round(final, 3),
            "accepted": final > 0.7
        }
    # ==================== CERTIFICATION MATCHING ====================
    
    def match_single_certification(self, job_cert_text: str, resume_cert_texts: List[str], threshold: float) -> float:
        """Returns best similarity score for a job certification against all resume certifications"""
        if not resume_cert_texts:
            return 0.0

        job_vec = self.embedder.embed_texts([job_cert_text])[0]
        resume_vecs = self.embedder.embed_texts(resume_cert_texts)

        similarities = [
            self.embedder.cosine_similarity(job_vec, r_vec)
            for r_vec in resume_vecs
        ]

        best_score = max(similarities)
        return best_score if best_score >= threshold else 0.0

    def evaluate_certification_group(self, group, resume_cert_texts: List[str], threshold: float) -> dict:
        """
        Evaluate a certification group with AND/OR/N_OF logic
        """
        cert_scores = []
        
        for cert_req in group.certifications:
            cert_name = cert_req.certification_name or ""
            text = cert_name.strip()
            
            if text:
                normalized_text = TextNormalizer.normalize(text)
                score = self.match_single_certification(normalized_text, resume_cert_texts, threshold)
                cert_scores.append(score)
            else:
                cert_scores.append(0.0)

        matched = sum(1 for s in cert_scores if s > 0)
        total = len(cert_scores)

        # Operator Logic
        if group.operator == "AND":
            base_score = sum(cert_scores) / total if total else 0.0
            coverage = matched / total if total else 0.0
            group_score = base_score * coverage
            passed = matched == total

        elif group.operator == "OR":
            group_score = max(cert_scores) if cert_scores else 0.0
            passed = matched >= 1

        elif group.operator == "N_OF":
            group_score = sum(cert_scores) / total if total else 0.0
            passed = matched >= (group.min_required or 1)

        else:
            group_score = sum(cert_scores) / total if total else 0.0
            passed = matched >= 1

        if group.min_required is not None:
            passed = matched >= group.min_required

        return {
            "group_score": round(group_score, 3),
            "matched_count": matched,
            "required_count": total,
            "passed": passed,
            "mandatory": group.mandatory
        }

    def match_certifications(self, resume_certifications: Certifications, job_certifications: CertificationRequirements) -> float:
        """Main certification matching with group logic"""
        if not resume_certifications or not resume_certifications.entries:
            return 0.0
        
        if not job_certifications or not job_certifications.groups:
            return 0.0
        
        # Prepare resume certification texts
        resume_texts = []
        for cert in resume_certifications.entries:
            cert_name = cert.certification_name or ""
            text = cert_name.strip()
            if text:
                resume_texts.append(TextNormalizer.normalize(text))
        
        if not resume_texts:
            return 0.0

        group_results = []
        penalty = 1.0

        for group in job_certifications.groups:
            result = self.evaluate_certification_group(group, resume_texts, self.SIMILARITY_THRESHOLD)
            group_results.append(result)

            # Mandatory group penalty
            if result["mandatory"] and not result["passed"]:
                penalty *= 0.6

        if not group_results:
            return 0.0

        avg_score = sum(g["group_score"] for g in group_results) / len(group_results)
        final_score = avg_score * penalty

        return float(round(final_score, 3))
    
    def extract_resume_certifications(self, resume_certifications: Certifications) -> List[str]:
        """Extract resume certifications for display"""
        if not resume_certifications or not resume_certifications.entries:
            return []
        
        cert_list = []
        for cert in resume_certifications.entries:
            cert_name = cert.certification_name or "Certification"
            issuer = cert.issuing_body or "Unknown Issuer"
            cert_list.append(f"{cert_name} ({issuer})")
        
        return cert_list
    
    def extract_job_certifications(self, job_certifications: CertificationRequirements) -> List[str]:
        """Extract job certification requirements for display"""
        if not job_certifications or not job_certifications.groups:
            return []
        
        cert_list = []
        for group in job_certifications.groups:
            for cert_req in group.certifications:
                cert_name = cert_req.certification_name or "Certification"
                issuer = cert_req.issuing_body or "Any Issuer"
                cert_list.append(f"{cert_name} ({issuer})")
        
        return cert_list

    # ==================== EXPERIENCE MATCHING ====================
    
    def extract_resume_experience(self, resume_experience: Experience) -> List[dict]:
        """Extract resume experience areas"""
        if not resume_experience or not resume_experience.experience_areas:
            return []
        return resume_experience.experience_areas
    
    def extract_job_experience(self, job_experiences: ExperienceRequirements) -> List[dict]:
        """Extract job experience requirements"""
        experiences = []
        if not job_experiences or not job_experiences.groups:
            return experiences

        for group in job_experiences.groups:
            for experience in group.experiences:
                experiences.append({
                    "experience_area": experience.experience_area,
                    "min_years": experience.min_years,
                    "max_years": experience.max_years,
                    "mandatory": group.mandatory,
                    "operator": group.operator,
                    "min_required": group.min_required
                })
        return experiences

    def match_experience_years(self, job_experiences: ExperienceRequirements, resume_experience: Experience) -> float:
        """Match experience with year validation and group logic"""
        if not job_experiences or not job_experiences.groups:
            return 0.0
        
        resume_items = self.extract_resume_experience(resume_experience)
        if not resume_items:
            return 0.0

        group_results = []
        penalty = 1.0

        for group in job_experiences.groups:
            exp_scores = []
            
            for job_exp in group.experiences:
                job_text = job_exp.experience_area
                resume_texts = [r.job_title for r in resume_items]
                
                job_vec = self.embedder.embed_texts([job_text])[0]
                resume_vecs = self.embedder.embed_texts(resume_texts)
                
                matched_years = 0.0
                
                for r_idx, resume_role in enumerate(resume_items):
                    sim = self.embedder.cosine_similarity(job_vec, resume_vecs[r_idx])
                    
                    if sim >= self.SIMILARITY_THRESHOLD:
                        matched_years = max(matched_years, resume_role.total_experience_years or 0)
                
                # Calculate score based on year requirements
                min_y = job_exp.min_years or 0
                max_y = job_exp.max_years
                
                if matched_years < min_y:
                    score = matched_years / min_y if min_y else 0.0
                elif max_y and matched_years > max_y:
                    score = max_y / matched_years
                else:
                    score = 1.0
                
                exp_scores.append(score)
            
            # Apply group operator logic
            matched = sum(1 for s in exp_scores if s > 0)
            total = len(exp_scores)
            
            if group.operator == "AND":
                base_score = sum(exp_scores) / total if total else 0.0
                coverage = matched / total if total else 0.0
                group_score = base_score * coverage
                passed = matched == total
            
            elif group.operator == "OR":
                group_score = max(exp_scores) if exp_scores else 0.0
                passed = matched >= 1
            
            elif group.operator == "N_OF":
                group_score = sum(exp_scores) / total if total else 0.0
                passed = matched >= (group.min_required or 1)
            
            else:
                group_score = sum(exp_scores) / total if total else 0.0
                passed = matched >= 1
            
            if group.min_required is not None:
                passed = matched >= group.min_required
            
            group_results.append({
                "group_score": group_score,
                "passed": passed,
                "mandatory": group.mandatory
            })
            
            # Apply penalty for failed mandatory groups
            if group.mandatory and not passed:
                penalty *= 0.6

        if not group_results:
            return 0.0

        avg_score = sum(g["group_score"] for g in group_results) / len(group_results)
        final_score = avg_score * penalty

        return float(round(final_score, 3))

    # ==================== RESPONSIBILITY MATCHING ====================
    
    def extract_resume_responsibilities(self, experience: Experience) -> List[str]:
        """Extract all responsibilities from resume experience"""
        responsibilities = []
        
        if not experience or not experience.experience_areas:
            return responsibilities
        
        for exp in experience.experience_areas:
            if exp.responsibilities:
                for resp in exp.responsibilities:
                    cleaned = resp.strip()
                    if cleaned:
                        responsibilities.append(cleaned)
        
        return responsibilities
    
    def match_responsibilities(self, experience: Experience, job: Job) -> float:
        """Match resume responsibilities against job responsibilities"""
        resume_responsibilities = self.extract_resume_responsibilities(experience)
        job_responsibilities = job.responsibilities
        
        if not job_responsibilities or not resume_responsibilities:
            return 0.0
        
        RESPONSIBILITY_THRESHOLD = 0.40
        total = len(job_responsibilities)
        
        job_vectors = self.embedder.embed_texts(job_responsibilities)
        resume_vectors = self.embedder.embed_texts(resume_responsibilities)
        
        matched_count = 0
        job_scores = []
        
        for job_vector in job_vectors:
            best_score = 0.0
            
            for resume_vec in resume_vectors:
                score = self.embedder.cosine_similarity(job_vector, resume_vec)
                best_score = max(score, best_score)
            
            if best_score < RESPONSIBILITY_THRESHOLD:
                best_score = 0.0
            else:
                matched_count += 1
            
            job_scores.append(best_score)
        
        final_score = sum(job_scores) / total
        
        return float(round(final_score, 3))

    # ==================== FINAL SCORE COMPUTATION ====================
    
    def compute_final_score(self, resume: Resume, job: Job, prefs: MatchingPreferences = None) -> Dict:
        """Compute final matching score with detailed breakdown"""
        resume = normalize_object(resume)
        job = normalize_object(job)
        
        if prefs is None:
            prefs = MatchingPreferences()
        
        # Calculate individual scores
        scores = {
            "skills": self.match_skills(resume, job),
            "experience": self.match_experience_years(job.experience_requirements, resume.experience),
            "education": self.match_education(resume.education, job.education_requirements),
            "certifications": self.match_certifications(resume.certifications, job.certification_requirements),
            "responsibilities": self.match_responsibilities(resume.experience, job)
        }
        
        # Weighted final score
        final = (
            scores["skills"] * prefs.skill_match_weight +
            scores["experience"] * prefs.experience_match_weight +
            scores["education"] * prefs.education_match_weight +
            scores["certifications"] * prefs.certification_match_weight +
            scores["responsibilities"] * prefs.responsibilities_match_weight
        )
        
        return {
            "scores": scores,
            "skill_details": {
                "resume_skills": self.extract_resume_skills(resume.skills),
                "job_skills": self.extract_job_skills(job.skill_requirements),
            },
            "education_details": {
                "resume_education": self.extract_resume_education(resume.education),
                "job_education": self.extract_job_education(job.education_requirements),
            },
            "certification_details": {
                "resume_certifications": self.extract_resume_certifications(resume.certifications),
                "job_certifications": self.extract_job_certifications(job.certification_requirements),
            },
            "final_match": round(final, 3),
            "accepted": final > 0.7
        }