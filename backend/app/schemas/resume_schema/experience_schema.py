from pydantic import BaseModel, Field
from typing import Optional,List
from .location import Location
class WorkExperience(BaseModel):
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
    total_experience_months:Optional[int]= None
    total_experience_years:Optional[float]= None
    extracted_keywords: Optional[List[str]]= None
    


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
