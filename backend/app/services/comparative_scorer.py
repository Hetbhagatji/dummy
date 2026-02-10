from typing import List, Dict, Tuple
from app.schemas.matching_result_schema import (
    MatchingResult, 
    AdditionalScores, 
    CategoryScores
)


class ComparativeScorer:
    """
    Calculates comparative scores across multiple candidates.
    
    Key Concept:
    - Additional scores are RELATIVE (compare candidates to each other)
    - Base scores are ABSOLUTE (compare candidate to job requirements)
    """
    
    # Configuration
    MAX_VALUABLE_EXCESS_YEARS = 5.0  # More than 5 extra years doesn't add much value
    
    # ==================== CALCULATE COMPOSITE EXCESS VALUES ====================
    
    @staticmethod
    def calculate_education_excess_value(excess_metrics) -> float:
        """
        Calculate education excess value weighted by degree level.
        
        Logic:
        - PhD = 3 points
        - Master's = 2 points
        - Bachelor's = 1 point
        - Diploma = 0.5 points
        
        Returns raw excess value (NOT normalized)
        """
        DEGREE_WEIGHTS = {
            "diploma": 0.5,
            "associate": 0.5,
            "bachelor's": 1.0,
            "bachelor": 1.0,
            "master's": 2.0,
            "master": 2.0,
            "mba": 2.0,
            "phd": 3.0,
            "doctorate": 3.0
        }
        
        if not excess_metrics.degree_levels:
            return 0.0
        
        # Calculate total weight of candidate's degrees
        total_weight = sum(
            DEGREE_WEIGHTS.get(level.lower().strip(), 1.0)
            for level in excess_metrics.degree_levels
        )
        
        # Subtract weight of required degrees (assume Bachelor's baseline = 1.0 per degree)
        required_weight = excess_metrics.required_degrees * 1.0
        
        # Excess value = candidate degrees - required degrees (in weighted points)
        excess_value = max(0.0, total_weight - required_weight)
        
        return excess_value
    
    @staticmethod
    def calculate_skills_excess_value(excess_metrics) -> float:
        """
        Calculate skills excess value.
        
        For now: Simple count approach.
        Future enhancement: Weight by category relevance.
        
        Returns raw excess value (NOT normalized)
        """
        return float(max(0, excess_metrics.excess_count))
    
    @staticmethod
    def calculate_experience_excess_value(excess_metrics) -> float:
        """
        Calculate experience excess value combining YEARS + BREADTH.
        
        Formula:
        - Years component (70%): Capped at 5 years max value
        - Areas component (30%): Bonus for extra areas, PENALTY for missing areas
        
        Returns composite value (can be negative if missing required areas)
        """
        
        # Component 1: Years (capped to avoid outliers)
        years_component = min(
            excess_metrics.excess_years, 
            ComparativeScorer.MAX_VALUABLE_EXCESS_YEARS
        ) / ComparativeScorer.MAX_VALUABLE_EXCESS_YEARS
        
        years_component = max(0.0, years_component)  # No negative years
        
        # Component 2: Areas (breadth)
        if excess_metrics.excess_areas >= 0:
            # Has extra areas beyond required → BONUS
            if excess_metrics.required_areas > 0:
                areas_component = excess_metrics.excess_areas / excess_metrics.required_areas
            else:
                areas_component = 0.0
        else:
            # Missing some required areas → PENALTY
            if excess_metrics.required_areas > 0:
                coverage = excess_metrics.matched_areas / excess_metrics.required_areas
                areas_component = -1.0 * (1.0 - coverage)  # Negative score
            else:
                areas_component = 0.0
        
        # Combine: 70% years, 30% breadth
        excess_value = (years_component * 0.7) + (areas_component * 0.3)
        
        return excess_value
    
    @staticmethod
    def calculate_certification_excess_value(excess_metrics) -> float:
        """
        Calculate certification excess value.
        Simple count (certifications are binary - have or don't have).
        
        Returns raw excess value (NOT normalized)
        """
        return float(max(0, excess_metrics.excess_count))
    
    # ==================== NORMALIZE ACROSS CANDIDATES ====================
    
    @staticmethod
    def normalize_scores(scores: List[float]) -> Tuple[List[float], Dict]:
        """
        Normalize scores to [0, 1] using min-max normalization.
        
        Formula: (score - min) / (max - min)
        
        Args:
            scores: List of raw scores
            
        Returns:
            Tuple of (normalized_scores [0-1], stats_dict)
        """
        
        if not scores:
            return [], {}
        
        min_score = min(scores)
        max_score = max(scores)
        mean_score = sum(scores) / len(scores)
        
        # Edge case: All candidates have same excess
        if max_score == min_score:
            # Everyone gets 0.0 (no one stands out)
            normalized = [0.0] * len(scores)
        else:
            # Standard min-max normalization
            normalized = [
                (score - min_score) / (max_score - min_score)
                for score in scores
            ]
        
        stats = {
            "min": round(min_score, 3),
            "max": round(max_score, 3),
            "mean": round(mean_score, 3)
        }
        
        return normalized, stats
    
    # ==================== CALCULATE ADDITIONAL SCORES (BATCH) ====================
    
    @staticmethod
    def calculate_additional_scores_batch(
        candidates: List[MatchingResult]
    ) -> Tuple[List[MatchingResult], Dict]:
        """
        Calculate and assign additional scores to ALL candidates.
        
        This is the KEY method - it:
        1. Calculates raw excess values for each candidate
        2. Normalizes across all candidates (0-1 scale)
        3. Assigns additional_scores to each candidate
        
        Args:
            candidates: List of MatchingResult objects
            
        Returns:
            Tuple of (updated_candidates, normalization_stats)
        """
        
        if not candidates:
            return [], {}
        
        # STEP 1: Calculate raw excess values for ALL candidates
        education_values = []
        skills_values = []
        experience_values = []
        certification_values = []
        
        for candidate in candidates:
            edu_val = ComparativeScorer.calculate_education_excess_value(
                candidate.excess_metrics.education
            )
            education_values.append(edu_val)
            
            skills_val = ComparativeScorer.calculate_skills_excess_value(
                candidate.excess_metrics.skills
            )
            skills_values.append(skills_val)
            
            exp_val = ComparativeScorer.calculate_experience_excess_value(
                candidate.excess_metrics.experience
            )
            experience_values.append(exp_val)
            
            cert_val = ComparativeScorer.calculate_certification_excess_value(
                candidate.excess_metrics.certifications
            )
            certification_values.append(cert_val)
        
        # STEP 2: Normalize across all candidates (0-1 scale)
        education_normalized, edu_stats = ComparativeScorer.normalize_scores(education_values)
        skills_normalized, skills_stats = ComparativeScorer.normalize_scores(skills_values)
        experience_normalized, exp_stats = ComparativeScorer.normalize_scores(experience_values)
        certification_normalized, cert_stats = ComparativeScorer.normalize_scores(certification_values)
        
        # STEP 3: Assign additional_scores to each candidate
        for i, candidate in enumerate(candidates):
            candidate.additional_scores = AdditionalScores(
                education_additional=round(education_normalized[i], 3),
                skills_additional=round(skills_normalized[i], 3),
                experience_additional=round(experience_normalized[i], 3),
                certifications_additional=round(certification_normalized[i], 3)
            )
        
        # Collect normalization stats for transparency
        normalization_stats = {
            "education": edu_stats,
            "skills": skills_stats,
            "experience": exp_stats,
            "certifications": cert_stats
        }
        
        return candidates, normalization_stats
    
    # ==================== CALCULATE CATEGORY SCORES ====================
    
    @staticmethod
    def calculate_category_scores(
        candidate: MatchingResult,
        base_weight: float = 0.70,
        additional_weight: float = 0.30
    ) -> CategoryScores:
        print('additional  score is ', additional_weight)
        """
        Combine base scores + additional scores for each category.
        
        Formula for each category:
        category_score = (base_score × base_weight) + (additional_score × additional_weight)
        
        Default: 70% base, 30% additional
        
        Args:
            candidate: MatchingResult with base_scores and additional_scores
            base_weight: Weight for base score (meeting requirements)
            additional_weight: Weight for additional score (extras)
            
        Returns:
            CategoryScores object with combined scores
        """
        
        if not candidate.additional_scores:
            # No additional scores - just use base scores
            return CategoryScores(
                skills=candidate.base_scores.skills,
                experience=candidate.base_scores.experience,
                education=candidate.base_scores.education,
                certifications=candidate.base_scores.certifications,
                responsibilities=candidate.base_scores.responsibilities
            )
        
        # Combine base + additional for each category
        return CategoryScores(
            skills=round(
                candidate.base_scores.skills * base_weight +
                candidate.additional_scores.skills_additional * additional_weight,
                3
            ),
            experience=round(
                candidate.base_scores.experience * base_weight +
                candidate.additional_scores.experience_additional * additional_weight,
                3
            ),
            education=round(
                candidate.base_scores.education * base_weight +
                candidate.additional_scores.education_additional * additional_weight,
                3
            ),
            certifications=round(
                candidate.base_scores.certifications * base_weight +
                candidate.additional_scores.certifications_additional * additional_weight,
                3
            ),
            responsibilities=candidate.base_scores.responsibilities  # No additional for responsibilities
        )
    
    # ==================== CALCULATE FINAL COMPARATIVE SCORE ====================
    
    @staticmethod
    def calculate_final_comparative_score(
        candidate: MatchingResult,
        category_weights: Dict[str, float]
    ) -> float:
        """
        Calculate weighted final score from category scores.
        
        Formula:
        final_score = Σ(category_score × category_weight)
        
        Args:
            candidate: MatchingResult with category_scores
            category_weights: Dict of weights for each category
            
        Returns:
            Final comparative score (0-1)
        """
        
        if not candidate.category_scores:
            # Fallback to base score if category scores not calculated
            return candidate.final_base_score
        
        final_score = (
            candidate.category_scores.skills * category_weights.get("skills", 0.5) +
            candidate.category_scores.experience * category_weights.get("experience", 0.25) +
            candidate.category_scores.education * category_weights.get("education", 0.15) +
            candidate.category_scores.certifications * category_weights.get("certifications", 0.05) +
            candidate.category_scores.responsibilities * category_weights.get("responsibilities", 0.05)
        )
        
        return round(final_score, 3)
    
    # ==================== COMPLETE RANKING PIPELINE ====================
    
    @staticmethod
    def rank_candidates(
        candidates: List[MatchingResult],
        base_weight: float = 0.70,
        additional_weight: float = 0.30,
        category_weights: Dict[str, float] = None
    ) -> Tuple[List[MatchingResult], Dict]:
        """
        Complete ranking pipeline - THIS IS THE MAIN METHOD TO USE!
        
        Pipeline:
        1. Calculate additional scores (normalized across all candidates)
        2. Calculate category scores (combine base + additional)
        3. Calculate final comparative scores
        4. Sort candidates by final score
        5. Assign ranks
        
        Args:
            candidates: List of MatchingResult objects
            base_weight: Weight for base scores (default 70%)
            additional_weight: Weight for additional scores (default 30%)
            category_weights: Weights for each category in final score
            
        Returns:
            Tuple of (ranked_candidates, normalization_stats)
        """
        
        if not candidates:
            return [], {}
        
        # Default category weights if not provided
        if category_weights is None:
            category_weights = {
                "skills": 0.5,
                "experience": 0.25,
                "education": 0.15,
                "certifications": 0.05,
                "responsibilities": 0.05
            }
        
        # STEP 1: Calculate additional scores (normalized across all candidates)
        candidates, norm_stats = ComparativeScorer.calculate_additional_scores_batch(candidates)
        
        # STEP 2: Calculate category scores for each candidate
        for candidate in candidates:
            candidate.category_scores = ComparativeScorer.calculate_category_scores(
                candidate,
                base_weight,
                additional_weight
            )
        
        # STEP 3: Calculate final comparative scores
        for candidate in candidates:
            candidate.final_comparative_score = ComparativeScorer.calculate_final_comparative_score(
                candidate,
                category_weights
            )
        
        # STEP 4: Sort by final comparative score (descending)
        candidates.sort(key=lambda c: c.final_comparative_score or 0.0, reverse=True)
        
        # STEP 5: Assign ranks
        for rank, candidate in enumerate(candidates, start=1):
            candidate.rank = rank
        
        return candidates, norm_stats