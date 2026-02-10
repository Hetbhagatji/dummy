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
from app.schemas.matching_result_schema import MatchingResult,BaseScores
from app.services.excess_calculator import ExcessCalculator

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

class SimilarityMatcher:
    def __init__(self):
        self.embedder = ResumeJobEmbedder()
        self.SIMILARITY_THRESHOLD = 0.6
        self.FIELD_SIMILARITY_THRESHOLD = 0.65
    
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
        skill_scores = []
        matched_skill_names = []  # ✅ NEW!

        for skill in group.skills:
            skill_name = TextNormalizer.normalize(skill.skill_name)
            score = self.match_single_skill(
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
    
    def match_skills(self, resume: Resume, job: Job) -> Dict:
        """Main skill matching with group logic - NO PENALTY
        
        Returns:
            {
                "score": float,
                "matched_skills": List[str],  # ✅ NEW!
                "total_required": int
            }
        """
        resume_skills = self.extract_resume_skills(resume.skills)
        
        if not job.skill_requirements or not job.skill_requirements.groups:
            return {"score": 0.0, "matched_skills": [], "total_required": 0}
        
        if not resume_skills:
            return {"score": 0.0, "matched_skills": [], "total_required": 0}

        group_results = []
        matched_skills_set = set()  # ✅ Track matched skills
        total_required = 0

        for group in job.skill_requirements.groups:
            result = self.evaluate_skill_group(group, resume_skills, self.SIMILARITY_THRESHOLD)
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
        """
        if not resume_levels or not job_levels:
            return False
        
        highest_resume_level = max(resume_levels)
        return any(highest_resume_level >= required_level for required_level in job_levels)

    def extract_resume_education(self, resume_education: Education) -> List[str]:
        """Extract resume education for display"""
        if not resume_education or not resume_education.entries:
            return []
        
        education_list = []
        for entry in resume_education.entries:
            level = entry.degree_level or "Unspecified Level"
            fields = ", ".join(entry.field) if entry.field else "No Fields"
            education_list.append(f"{level}: {fields}")
        return education_list

    def extract_job_education(self, job_education: EducationRequirements) -> List[str]:
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
    
    def extract_resume_degree_combinations(self, resume_education) -> List[tuple]:
        """Extract degree combinations as (level, field) pairs"""
        if not resume_education or not resume_education.entries:
            return []
        
        combinations = []
        for entry in resume_education.entries:
            level = self.normalize_level(entry.degree_level)
            if entry.field:
                for field in entry.field:
                    cleaned_field = TextNormalizer.normalize(field.strip())
                    if cleaned_field and level:
                        # Store as tuple: (level, field)
                        combinations.append((level, cleaned_field))
        return combinations

    def match_single_degree_combination(self, job_level: str, job_field: str, 
                                    resume_combinations: List[tuple], 
                                    threshold: float) -> float:
        """Match a job requirement (level+field) against resume degree combinations"""
        if not resume_combinations:
            return 0.0
        
        # Create combined string for job requirement
        job_combined = f"{job_level} in {job_field}"
        job_vec = self.embedder.embed_texts([job_combined])[0]
        
        # Create combined strings for all resume combinations
        resume_combined_texts = [
            f"{level} in {field}" for level, field in resume_combinations
        ]
        resume_vecs = self.embedder.embed_texts(resume_combined_texts)
        
        # Find best match
        similarities = [
            self.embedder.cosine_similarity(job_vec, r_vec)
            for r_vec in resume_vecs
        ]
        
        best_score = max(similarities)
        return best_score if best_score >= threshold else 0.0

    def evaluate_education_group(self, group, resume_combinations: List[tuple]) -> dict:
        """Evaluate SINGLE group with AND/OR/N_OF logic"""
        degree_scores = []
        
        for degree_req in group.degrees:
            level = self.normalize_level(degree_req.degree_level)
            field_scores = []
            
            for job_field in degree_req.fields:
                normalized_job_field = TextNormalizer.normalize(job_field)
                # Match complete degree combination
                best_score = self.match_single_degree_combination(
                    level, normalized_job_field, resume_combinations, 
                    self.FIELD_SIMILARITY_THRESHOLD
                )
                field_scores.append(best_score)
            
            degree_score = sum(field_scores) / len(field_scores) if field_scores else 0.0
            degree_scores.append(degree_score)
        
        matched = sum(1 for s in degree_scores if s >= self.FIELD_SIMILARITY_THRESHOLD)
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

    def match_education(self, resume_education: Education, job_education: EducationRequirements) -> float:
        """Main education matching: LEVEL FIRST → GROUP LOGIC → NO PENALTY"""
        if not job_education or not job_education.groups:
            return 1.0
        if not resume_education or not resume_education.entries:
            return 0.0
        
        # STEP 1: LEVEL CHECK (Global gate)
        resume_levels = self.extract_resume_levels(resume_education)
        job_levels = self.extract_job_levels(job_education)
        
        if not self.check_level_capability(resume_levels, job_levels):
            return 0.0
        
        # STEP 2: Extract degree combinations (level + field pairs)
        resume_combinations = self.extract_resume_degree_combinations(resume_education)
        group_results = []

        for group in job_education.groups:
            group_score = self.evaluate_education_group(group, resume_combinations)
            group_results.append(group_score)

        if not group_results:
            return 0.0
        
        # STEP 3: Average group scores
        avg_score = sum(g["group_score"] for g in group_results) / len(group_results)

        return float(round(avg_score, 3))
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
        """Evaluate a certification group with AND/OR/N_OF logic"""
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

        if group.operator == "AND":
            base_score = sum(cert_scores) / total if total else 0.0
            coverage = matched / total if total else 0.0
            group_score = base_score 
            passed = matched == total

        elif group.operator == "OR":
            if not cert_scores:
                group_score = 0.0
            else:
                best_score = max(cert_scores)
                coverage = matched / total if total else 0.0
                # 70% from best match + 30% bonus for breadth
                group_score = (best_score * 0.7) + (coverage * 0.3)
            passed = matched >= 1

        elif group.operator == "N_OF":
            min_req = group.min_required or 1
            # Base score from average
            base_score = sum(cert_scores) / total if total else 0.0
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
            group_score = sum(cert_scores) / total if total else 0.0
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

    def match_certifications(self, resume_certifications: Certifications, job_certifications: CertificationRequirements) -> float:
        """Main certification matching - NO PENALTY"""
        if not job_certifications or not job_certifications.groups:
            return 1.0
        
        if not resume_certifications or not resume_certifications.entries:
            return 0.0
        
        resume_texts = []
        for cert in resume_certifications.entries:
            cert_name = cert.certification_name or ""
            text = cert_name.strip()
            if text:
                resume_texts.append(TextNormalizer.normalize(text))
        
        if not resume_texts:
            return 0.0

        group_results = []

        for group in job_certifications.groups:
            result = self.evaluate_certification_group(group, resume_texts, self.SIMILARITY_THRESHOLD)
            group_results.append(result)
            # ❌ PENALTY REMOVED

        if not group_results:
            return 0.0

        avg_score = sum(g["group_score"] for g in group_results) / len(group_results)

        return float(round(avg_score, 3))
    
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
    
    def match_experience(self, job_requirements: ExperienceRequirements,resume_experience: Experience) -> Dict:
        if not job_requirements or not job_requirements.groups:
            return self._empty_result("No job requirements")
        
        if not resume_experience or not resume_experience.experience_areas:
            return self._empty_result("No resume experience")
        
        # Process all groups
        group_results = []
        all_match_details = []
        
        for group_idx, group in enumerate(job_requirements.groups):
            group_result = self._process_group(
                group, 
                resume_experience.experience_areas,
                group_idx
            )
            group_results.append(group_result['score'])
            all_match_details.extend(group_result['matches'])
        
        # Calculate final score (average of all groups)
        final_score = sum(group_results) / len(group_results) if group_results else 0.0
        
        return {
            "score": round(final_score, 3),
            "details": all_match_details,
            "group_scores": [round(s, 3) for s in group_results],
            "total_groups": len(group_results)
        }
    
    # ==================== GROUP PROCESSING ====================
    
    def _process_group(self, group, resume_jobs: List, group_idx: int) -> Dict:
        """Process a single requirement group (AND/OR logic)"""
        
        requirement_scores = []
        match_details = []
        
        # Process each requirement in the group
        for req_idx, requirement in enumerate(group.experiences):
            
            # Find best matching resume job
            best_match = self._find_best_match(
                requirement.experience_area,
                requirement.min_years,
                requirement.max_years,
                resume_jobs
            )
            
            requirement_scores.append(best_match['score'])
            match_details.append({
                "group": group_idx + 1,
                "requirement": requirement.experience_area,
                "min_years": requirement.min_years,
                "max_years": requirement.max_years,
                **best_match
            })
        
        matched = sum(1 for s in requirement_scores if s > 0)
        total = len(requirement_scores)
        
        # Apply group operator logic
        if group.operator == "AND":
            group_score = sum(requirement_scores) / total if total else 0.0
        
        elif group.operator == "OR":
            if not requirement_scores:
                group_score = 0.0
            else:
                best_score = max(requirement_scores)
                coverage = matched / total if total else 0.0
                group_score = (best_score * 0.7) + (coverage * 0.3)
        
        else:
            group_score = sum(requirement_scores) / total if total else 0.0

        # ✅ OUTSIDE all blocks (unindent by 4 spaces)
        return {
            "score": group_score,
            "matches": match_details
        }
        
        
    # ==================== BEST MATCH FINDER ====================
    
    def _find_best_match(self, experience_area: str, min_years: float, max_years: float, resume_jobs: List) -> Dict:
        """
        Find the best matching resume job for a requirement
        
        Logic:
        1. Compare experience_area with extracted_keywords + job_title
        2. If similarity >= threshold, calculate year score
        3. Final score = similarity × year_score
        """
        
        best_score = 0.0
        best_match_info = None
        
        # Check each resume job
        for job in resume_jobs:
            
            # Get keywords from this job
            keywords = job.extracted_keywords if hasattr(job, 'extracted_keywords') else []
            
            # ✅ ADD JOB TITLE TO KEYWORDS
            combined_keywords = keywords.copy() if keywords else []
            
            # Add job title as additional keyword
            if hasattr(job, 'job_title') and job.job_title:
                combined_keywords.append(job.job_title)
            
            # Skip if no keywords at all
            if not combined_keywords:
                continue
            
            # Calculate similarity between requirement and ALL keywords (including job title)
            similarity = self._calculate_keyword_similarity(experience_area, combined_keywords)
            
            # Only proceed if similarity meets threshold
            if similarity >= self.SIMILARITY_THRESHOLD:
                
                # Calculate year score
                years = job.total_experience_years or 0.0
                year_score = self._calculate_year_score(years, min_years, max_years)
                
                # Combined score
                combined_score = similarity * year_score
                
                # Keep best match
                if combined_score > best_score:
                    best_score = combined_score
                    best_match_info = {
                        "matched_job": job.job_title,
                        "company": job.company_name,
                        "matched_keywords": combined_keywords,  # ✅ Now includes job title
                        "similarity": round(similarity, 3),
                        "years": years,
                        "year_score": round(year_score, 3),
                        "score": round(combined_score, 3)
                    }
        
        # Return result
        if best_match_info:
            return best_match_info
        else:
            return {
                "matched_job": None,
                "company": None,
                "matched_keywords": [],
                "similarity": 0.0,
                "years": 0.0,
                "year_score": 0.0,
                "score": 0.0
            }
    
    # ==================== SIMILARITY CALCULATION ====================
    
    def _calculate_keyword_similarity(
        self, 
        experience_area: str, 
        keywords: List[str]
    ) -> float:
        """
        Calculate similarity between requirement and extracted keywords
        Returns the BEST similarity among all keywords
        """
        if not keywords:
            return 0.0
        
        # Embed the requirement
        req_vec = self.embedder.embed_texts([experience_area])[0]
        
        # Embed all keywords
        keyword_vecs = self.embedder.embed_texts(keywords)
        
        # Find best similarity
        best_sim = 0.0
        for kw_vec in keyword_vecs:
            sim = self.embedder.cosine_similarity(req_vec, kw_vec)
            best_sim = max(best_sim, sim)
        
        return float(best_sim)
    
    # ==================== YEAR SCORE CALCULATION ====================
    
    def _calculate_year_score(
        self,
        actual_years: float,
        min_years: float,
        max_years: float = None
    ) -> float:
        """
        Calculate score based on years of experience
        
        Cases:
        1. actual >= min AND (no max OR actual <= max) → 1.0 (perfect)
        2. actual < min → actual/min (partial credit)
        3. actual > max (if max exists) → max/actual (overqualified penalty)
        """
        
        min_y = min_years or 0.0
        
        # Case 1: Meets minimum requirement
        if actual_years >= min_y:
            # Check if there's a maximum
            if max_years and actual_years > max_years:
                # Overqualified - apply slight penalty
                return max_years / actual_years
            else:
                # Perfect match
                return 1.0
        
        # Case 2: Below minimum - give partial credit
        else:
            if min_y > 0:
                return actual_years / min_y
            else:
                return 0.0
    
    # ==================== HELPER METHODS ====================
    
    def _empty_result(self, reason: str) -> Dict:
        """Return empty result with reason"""
        return {
            "score": 0.0,
            "details": [],
            "group_scores": [],
            "total_groups": 0,
            "reason": reason
        }
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
        """Compute final matching score with FULL experience details"""
        resume = normalize_object(resume)
        job = normalize_object(job)
        
        if prefs is None:
            prefs = MatchingPreferences()
        
        # Calculate individual scores
        experience_result = self.match_experience(job.experience_requirements, resume.experience)
        skills_result = self.match_skills(resume, job)
        scores = {
            "skills": skills_result["score"],
            "experience": experience_result["score"],
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
            "**NEW**_experience_details": experience_result,  # ✅ DETAILED MATCHES!
            "certification_details": {
                "resume_certifications": self.extract_resume_certifications(resume.certifications),
                "job_certifications": self.extract_job_certifications(job.certification_requirements),
            },
            "final_match": float(round(final, 3)),
            "accepted": final > 0.7,
            "matched_skills": skills_result["matched_skills"],  # ✅ NEW!
            "total_required": skills_result["total_required"]
        }
    def compute_final_score_with_excess(self, resume: Resume, job: Job, prefs: MatchingPreferences = None) -> MatchingResult:
        # Call existing method
        old_result = self.compute_final_score(resume, job, prefs)
        
        # Extract matched skills list (you'll need to store this from match_skills)
        # ✅ Extract ONLY the matched required skills
        matched_skills = old_result.get("matched_skills", [])
        total_required_skills = old_result.get("total_required", 0)
        exp_details = old_result.get("**NEW**_experience_details", {})
        matched_areas_count = sum(
            1 for detail in exp_details.get("details", []) 
            if detail.get("matched_job") is not None
        )
        
        # Calculate excess metrics
        excess_metrics = ExcessCalculator.calculate_all_excess(
            resume=resume,
            job=job,
            matched_skills=matched_skills,  # ✅ Now contains ONLY matched skills
            matched_areas_count=matched_areas_count,
            total_required_skills=total_required_skills
        )
        
        # Create base scores
        base_scores = BaseScores(
            skills=old_result["scores"]["skills"],
            experience=old_result["scores"]["experience"],
            education=old_result["scores"]["education"],
            certifications=old_result["scores"]["certifications"],
            responsibilities=old_result["scores"]["responsibilities"]
        )
        
        # Create matching result
        result = MatchingResult(
            candidate_id=resume.resume_id or "unknown",
            job_id=job.job_id or "unknown",
            base_scores=base_scores,
            excess_metrics=excess_metrics,
            final_base_score=old_result["final_match"],
            is_qualified=old_result["accepted"],
            matching_preferences=prefs.dict() if prefs else None
        )
        
        return result