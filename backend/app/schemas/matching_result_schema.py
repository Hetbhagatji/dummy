from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from app.schemas.SkillsExcess import SkillsExcess


# ==================== BASE SCORES ====================

class BaseScores(BaseModel):
    """Base matching scores. Always in [0.0, 1.0]."""
    skills: float = Field(ge=0.0, le=1.0)
    experience: float = Field(ge=0.0, le=1.0)
    education: float = Field(ge=0.0, le=1.0)
    certifications: float = Field(ge=0.0, le=1.0)
    responsibilities: float = Field(ge=0.0, le=1.0)


# ==================== EXCESS METRICS ====================

class EducationExcessMetrics(BaseModel):
    """Tracks education beyond requirements."""
    required_degrees: int
    candidate_degrees: int = Field(description="Raw count including duplicates")
    excess_count: int = Field(description="Can be negative (deficit)")
    degree_levels: List[str] = Field(description="UNIQUE degree levels (deduplicated by ExcessCalculator)")


class SkillsExcessMetrics(BaseModel):
    """Tracks skills beyond requirements."""
    required_skills_count: int
    matched_skills_count: int
    excess_count: int = Field(description="Can be negative (deficit)")


class ExperienceExcessMetrics(BaseModel):
    """Tracks experience beyond requirements."""
    required_years: float = Field(description="SUM of min_years across all required areas")
    candidate_years: float
    excess_years: float = Field(description="Floored at 0")
    required_areas: int
    matched_areas: int
    excess_areas: int = Field(description="Can be negative when required areas unmatched")


class CertificationExcessMetrics(BaseModel):
    """Tracks certifications beyond requirements."""
    required_certs: int
    candidate_certs: int
    excess_count: int = Field(description="Can be negative (deficit)")
    extra_certs: Optional[List[str]] = Field(None)


class ExcessMetrics(BaseModel):
    """Complete excess metrics for a candidate."""
    education: EducationExcessMetrics
    skills: SkillsExcess
    experience: ExperienceExcessMetrics
    certifications: CertificationExcessMetrics


# ==================== ADDITIONAL SCORES (NORMALIZED) ====================

class AdditionalScores(BaseModel):
    """
    Normalised tiebreaker scores relative to all candidates.

    Range: [-1.0, +1.0]
        +1.0 = best in batch for this dimension  → gets maximum bonus
         0.0 = middle of batch OR all tied       → no change to score
        -1.0 = worst in batch for this dimension → gets maximum penalty

    This [-1, +1] scale is intentional:
        The candidate with the MOST excess (e.g. most extra skills) keeps
        their score at maximum.  Candidates with LESS excess get their score
        REDUCED proportionally.  This differentiates tied candidates where
        base scores alone cannot.

    The penalty is bounded by additional_weight (default 0.10), so a
    candidate can lose at most 0.10 from their base score.
    final_comparative_score is hard-clamped to [0.0, 1.0].
    """
    education_additional: float = Field(ge=-1.0, le=1.0)
    skills_additional: float = Field(ge=-1.0, le=1.0)
    experience_additional: float = Field(ge=-1.0, le=1.0)
    certifications_additional: float = Field(ge=-1.0, le=1.0)


# ==================== CATEGORY SCORES (DISPLAY ONLY) ====================

class CategoryScores(BaseModel):
    """
    Combined per-category scores for display purposes only. Always in [0.0, 1.0].

    Formula:
        category_score = clamp(base_score + additional_norm × additional_weight, 0.0, 1.0)

    FIX: Previously these were NOT clamped, producing values like 1.1 in the
    API response which was confusing.  The clamping is safe because
    final_comparative_score is computed from RAW base_scores + additional_scores,
    not from these display scores — so no information is lost.
    """
    skills: float = Field(ge=0.0, le=1.0)
    experience: float = Field(ge=0.0, le=1.0)
    education: float = Field(ge=0.0, le=1.0)
    certifications: float = Field(ge=0.0, le=1.0)
    responsibilities: float = Field(ge=0.0, le=1.0)


# ==================== MATCHING RESULT (SINGLE CANDIDATE) ====================

class MatchingResult(BaseModel):
    """Complete matching result for ONE candidate against ONE job."""

    candidate_id: str
    job_id: str
    matched_at: datetime = Field(default_factory=datetime.utcnow)

    base_scores: BaseScores
    excess_metrics: ExcessMetrics

    additional_scores: Optional[AdditionalScores] = Field(
        None,
        description="[-1, +1] tiebreaker scores. Only set during batch ranking."
    )

    category_scores: Optional[CategoryScores] = Field(
        None,
        description="Display scores clamped to [0, 1]. Only set during batch ranking."
    )

    final_base_score: float = Field(
        ge=0.0, le=1.0,
        description="Weighted sum of base_scores only. Always in [0, 1]."
    )

    final_comparative_score: Optional[float] = Field(
        None,
        ge=0.0, le=1.0,
        description="Final score including tiebreaker. Always in [0, 1]."
    )

    rank: Optional[int] = Field(None, description="Rank among all candidates (1 = best)")

    is_qualified: bool
    qualification_threshold: float = Field(default=0.70)
    matching_preferences: Optional[Dict] = Field(None)


# ==================== BATCH RESULT ====================

class ComparativeRankingResult(BaseModel):
    """Result of comparative ranking for multiple candidates."""
    job_id: str
    total_candidates: int
    ranked_at: datetime = Field(default_factory=datetime.utcnow)
    candidates: List[MatchingResult]
    normalization_stats: Dict
    base_weight: float = Field(default=0.90)
    additional_weight: float = Field(default=0.10)


# ==================== NORMALIZATION STATS ====================

class NormalizationStats(BaseModel):
    education: Dict[str, float]
    skills: Dict[str, float]
    experience: Dict[str, float]
    certifications: Dict[str, float]