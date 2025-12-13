from pydantic import BaseModel,model_validator

class WeightSchema(BaseModel):
    summary_weight: float = 0.25
    experience_weight: float = 0.30
    skills_weight: float = 0.25
    education_weight: float = 0.10
    location_weight: float = 0.05
    achievements_weight: float = 0.05
    
    
    @model_validator(mode="after")
    def validate_total_weight(self):
        total = (
            self.summary_weight
            + self.experience_weight
            + self.skills_weight
            + self.education_weight
            + self.location_weight
            + self.achievements_weight
        )

        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Total weight must be exactly 1.0, received {round(total, 4)}"
            )

        return self
