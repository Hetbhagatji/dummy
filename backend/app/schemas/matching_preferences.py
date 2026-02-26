from pydantic import BaseModel, Field, model_validator

class MatchingPreferences(BaseModel):
    skill_match_weight: float = Field(0.50, ge=0.0, le=1.0)
    experience_match_weight: float = Field(0.25, ge=0.0, le=1.0)
    education_match_weight: float = Field(0.15, ge=0.0, le=1.0)
    certification_match_weight: float = Field(0.05, ge=0.0, le=1.0)
    responsibilities_match_weight: float = Field(0.05, ge=0.0, le=1.0)
    
    def to_category_weights(self) -> dict:
        return {
            "skills":           self.skill_match_weight,
            "experience":       self.experience_match_weight,
            "education":        self.education_match_weight,
            "certifications":   self.certification_match_weight,
            "responsibilities": self.responsibilities_match_weight,
        }

    @model_validator(mode="after")
    def weights_must_sum_to_one(self) -> "MatchingPreferences":
        total = round(
            self.skill_match_weight
            + self.experience_match_weight
            + self.education_match_weight
            + self.certification_match_weight
            + self.responsibilities_match_weight,
            6,
        )
        if abs(total - 1.0) > 1e-4:
            raise ValueError(
                f"All weights must sum to 1.0, got {total}. "
                "Adjust your values before submitting."
            )
        return self