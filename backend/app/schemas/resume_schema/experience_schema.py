from pydantic import BaseModel, Field,field_validator
from typing import Optional,List
from .location import Location
from app.schemas.job_schema import SkillRequirement
from app.schemas.null_validator import NullSafeValidator
class WorkExperience(NullSafeValidator,BaseModel):
    job_title: Optional[str] = Field(
        None,
        description="Job title for any industry: Software Engineer, Clinical Research Associate, Financial Analyst, Pharmacist, Nurse, etc."
    )
    company_name: Optional[str] = None
    location: Optional[Location] = None
    employment_type: Optional[str] = Field(
        None,
        description="Full-time, Part-time, Contract, Internship, Fellowship"
    )
    start_date: Optional[str] = None
    end_date: Optional[str] = Field(
        None,
        description="End date or 'Present' if current"
    )
    responsibilities: Optional[List[str]] = Field(
        default_factory=list,
        description="Responsibilities and achievements for any role"
    )
    skills : Optional[List[SkillRequirement]] = Field(default_factory=list)
    total_experience_months:Optional[int]= None
    total_experience_years:Optional[float]= None
    extracted_keywords: Optional[List[str]]=  Field(default_factory=list)
    
    @field_validator('skills', mode='before')
    @classmethod
    def fix_skills(cls, v):
        if v is None or (isinstance(v, str) and v.strip().lower() in {"null", "none", ""}):
            return []
        return v

    @field_validator('total_experience_months', mode='before')
    @classmethod
    def fix_months(cls, v):
        if v is None or (isinstance(v, str) and v.strip().lower() in {"null", "none", ""}):
            return None
        return v

    @field_validator('total_experience_years', mode='before')
    @classmethod
    def fix_years(cls, v):
        if v is None or (isinstance(v, str) and v.strip().lower() in {"null", "none", ""}):
            return None
        return v
    


class Experience(BaseModel):
    experience_areas: List[WorkExperience] = Field(
        default_factory=list
    )
    # total_experience_months: Optional[str] = Field(
    #     None,
    #     description="Total work experience in months"
    # )
    # total_experience_years: Optional[str] = Field(
    #     None,
    #     description="Total experience in years (rounded to 1 decimal)"
    # )
