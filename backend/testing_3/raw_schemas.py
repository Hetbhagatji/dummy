from pydantic import BaseModel
from typing import Optional

class RawJobData(BaseModel):
    job_title_text: Optional[str] = None
    company_details_text: Optional[str] = None
    industry_text: Optional[str] = None  
    raw_locations_text: Optional[str] = None
    raw_experience_text: Optional[str] = None
    raw_education_requirements_text: Optional[str] = None
    raw_skills_text: Optional[str] = None
    raw_certifications_text: Optional[str] = None
    raw_responsibilities_text: Optional[str] = None
    raw_soft_skills_text: Optional[str] = None
    raw_salary_text: Optional[str] = None
