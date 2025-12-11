from pydantic import BaseModel

class WeightSchema(BaseModel):
    summary_weight: float = 0.25
    experience_weight: float = 0.30
    skills_weight: float = 0.25
    education_weight: float = 0.10
    location_weight: float = 0.05
    achievements_weight: float = 0.05
