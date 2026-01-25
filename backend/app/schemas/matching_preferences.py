from pydantic import BaseModel,Field


# Default values (sums to 1.0)
class MatchingPreferences(BaseModel):
    skill_match_weight: float = Field(0.5,  ge=0.0, le=1.0)    # Skills most important
    experience_match_weight: float = Field(0.25, ge=0.0, le=1.0)
    education_match_weight: float = Field(0.15, ge=0.0, le=1.0)
    certification_match_weight: float = Field(0.05, ge=0.0, le=1.0)
    responsibilities_match_weight: float = Field(0.05, ge=0.0, le=1.0)
    
