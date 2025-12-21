from pydantic import BaseModel,Field
from typing import List,Optional
from .certifications_schema import Certifications
from .education_schema import Education
from .experience_schema import WorkHistory
from .personal_information_schema import PersonalInfo
from .skills_schema import Skills
class Resume(BaseModel):
    resume_id: Optional[str] = None
    
    personal_info: PersonalInfo
    
    education: Education
    
    work_history: WorkHistory
    
    skills: Skills
    
    certifications: Optional[Certifications] = None
    

    
    raw_text: Optional[str] = Field(
        None,
        description="Original resume text"
    )
    
    parsed_date: Optional[str] = Field(
        None,
        description="When this resume was parsed"
    )
    
    industry_domain: Optional[str] = Field(
        None,
        description="Primary industry domain of the candidate based on their experience and skills (e.g., Pharmaceutical, Healthcare, Banking, Finance, Information Technology, Software Development, Manufacturing, Retail, Education, etc.)"
    )