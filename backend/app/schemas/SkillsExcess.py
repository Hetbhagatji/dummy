from pydantic import BaseModel
from typing import Optional, List
class SkillsExcess(BaseModel):
    required_skills_count: int
    matched_skills_count: int
    matched_required_count: int
    missing_required_count: int
    bonus_skills_count: int
    excess_count: int  # ✅ Good - this exists!