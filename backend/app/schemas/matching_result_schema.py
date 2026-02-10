from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.schemas.SkillsExcess import SkillsExcess

# ==================== BASE SCORES ====================

class BaseScores(BaseModel):
    """Base matching scores (current system output)"""
    skills: float = Field(ge=0.0, le=1.0)
    experience: float = Field(ge=0.0, le=1.0)
    education: float = Field(ge=0.0, le=1.0)
    certifications: float = Field(ge=0.0, le=1.0)
    responsibilities: float = Field(ge=0.0, le=1.0)


# ==================== EXCESS METRICS ====================

class EducationExcessMetrics(BaseModel):
    """Tracks education beyond requirements"""
    required_degrees: int = Field(description="Number of degrees job requires")
    candidate_degrees: int = Field(description="Number of degrees candidate has")
    excess_count: int = Field(description="Excess degrees (candidate - required)")
    degree_levels: List[str] = Field(description="All degree levels candidate has")
    
    # # Weighted excess (optional - for advanced scoring)
    # weighted_excess: Optional[float] = Field(
    #     None, 
    #     description="Weighted by level: PhD=3, Master=2, Bachelor=1"
    # )


class SkillsExcessMetrics(BaseModel):
    """Tracks skills beyond requirements"""
    required_skills_count: int = Field(description="Total minimum skills needed")
    matched_skills_count: int = Field(description="Total skills candidate has that match")
    excess_count: int = Field(description="Extra matched skills")
    
    # # Per-group breakdown
    # group_excesses: List[int] = Field(
    #     description="Excess per group: [group1_excess, group2_excess, ...]"
    # )
    
    # # Optional: list of extra skill names
    # extra_skills: Optional[List[str]] = Field(None)


class ExperienceExcessMetrics(BaseModel):
    """Tracks experience beyond requirements"""
    required_years: float = Field(description="Minimum years required")
    candidate_years: float = Field(description="Total years candidate has")
    excess_years: float = Field(description="Years beyond minimum")
    
    # Area coverage
    required_areas: int = Field(description="Number of experience areas required")
    matched_areas: int = Field(description="Number of areas candidate matches")
    excess_areas: int = Field(
        description="Extra areas beyond required (can be 0 or negative)"
    )


class CertificationExcessMetrics(BaseModel):
    """Tracks certifications beyond requirements"""
    required_certs: int = Field(description="Number of certs required")
    candidate_certs: int = Field(description="Number of certs candidate has")
    excess_count: int = Field(description="Extra certifications")
    
    # Optional: list of extra cert names
    extra_certs: Optional[List[str]] = Field(None)


class ExcessMetrics(BaseModel):
    """Complete excess metrics for a candidate"""
    education: EducationExcessMetrics
    skills: SkillsExcess
    experience: ExperienceExcessMetrics
    certifications: CertificationExcessMetrics


# ==================== ADDITIONAL SCORES (NORMALIZED) ====================

class AdditionalScores(BaseModel):
    """Normalized additional scores (0.0 to 1.0) relative to all candidates"""
    education_additional: float = Field(
        ge=0.0, le=1.0,
        description="Normalized excess education score"
    )
    skills_additional: float = Field(
        ge=0.0, le=1.0,
        description="Normalized excess skills score"
    )
    experience_additional: float = Field(
        ge=0.0, le=1.0,
        description="Normalized excess experience score"
    )
    certifications_additional: float = Field(
        ge=0.0, le=1.0,
        description="Normalized excess certifications score"
    )


# ==================== CATEGORY SCORES (BASE + ADDITIONAL) ====================

class CategoryScores(BaseModel):
    """Combined scores per category (base + additional)"""
    skills: float = Field(ge=0.0, le=1.0)
    experience: float = Field(ge=0.0, le=1.0)
    education: float = Field(ge=0.0, le=1.0)
    certifications: float = Field(ge=0.0, le=1.0)
    responsibilities: float = Field(ge=0.0, le=1.0)


# ==================== MATCHING RESULT (SINGLE CANDIDATE) ====================

class MatchingResult(BaseModel):
    """Complete matching result for ONE candidate against ONE job"""
    
    # Identifiers
    candidate_id: str = Field(description="Unique candidate/resume ID")
    job_id: str = Field(description="Unique job ID")
    
    # Timestamps
    matched_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Base matching (your current system)
    base_scores: BaseScores
    
    # Excess metrics (raw counts/values)
    excess_metrics: ExcessMetrics
    
    # Additional scores (normalized across all candidates) - ONLY for comparative ranking
    additional_scores: Optional[AdditionalScores] = Field(
        None,
        description="Only populated when doing comparative ranking"
    )
    
    # Combined scores (only for comparative ranking)
    category_scores: Optional[CategoryScores] = Field(
        None,
        description="base + additional combined, only for comparative ranking"
    )
    
    # Final scores
    final_base_score: float = Field(
        ge=0.0, le=1.0,
        description="Weighted final from base scores only"
    )
    
    final_comparative_score: Optional[float] = Field(
        None,
        ge=0.0, le=1.0,
        description="Final score including additional bonuses (comparative ranking)"
    )
    
    # Ranking (only meaningful in batch context)
    rank: Optional[int] = Field(None, description="Rank among all candidates")
    
    # Status
    is_qualified: bool = Field(description="Meets minimum requirements (base_score >= threshold)")
    qualification_threshold: float = Field(default=0.70)
    
    # Metadata
    matching_preferences: Optional[Dict] = Field(
        None,
        description="Weights used for this match"
    )


# ==================== BATCH RESULT (MULTIPLE CANDIDATES) ====================

class ComparativeRankingResult(BaseModel):
    """Result of comparative ranking for multiple candidates"""
    
    job_id: str
    total_candidates: int
    ranked_at: datetime = Field(default_factory=datetime.utcnow)
    
    # All candidates with their results
    candidates: List[MatchingResult]
    
    # Normalization metadata (for transparency)
    normalization_stats: Dict = Field(
        description="Min/max values used for normalization per category"
    )
    
    # Configuration used
    base_weight: float = Field(default=0.70)
    additional_weight: float = Field(default=0.30)
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "job_456",
                "total_candidates": 10,
                "candidates": [
                    {
                        "candidate_id": "123",
                        "rank": 1,
                        "final_comparative_score": 0.823
                    }
                ]
            }
        }


# ==================== NORMALIZATION STATS ====================

class NormalizationStats(BaseModel):
    """Statistics used for normalizing excess metrics"""
    
    education: Dict[str, float] = Field(
        description="{'min': 0, 'max': 3, 'mean': 1.2}"
    )
    skills: Dict[str, float]
    experience: Dict[str, float]
    certifications: Dict[str, float]
    
    class Config:
        json_schema_extra = {
            "example": {
                "education": {"min": 0, "max": 3, "mean": 1.2, "median": 1},
                "skills": {"min": 0, "max": 15, "mean": 6.5, "median": 5},
                "experience": {"min": 0, "max": 10, "mean": 3.2, "median": 2},
                "certifications": {"min": 0, "max": 5, "mean": 1.8, "median": 1}
            }
        }