from pydantic import BaseModel,Field
from typing import List,Optional
from .certifications_schema import Certifications
from .education_schema import Education
from .experience_schema import Experience
from .personal_information_schema import PersonalInfo
from .skills_schema import Skills
from .job_metadata import JobMetadata
class Resume(BaseModel):
    resume_id: Optional[str] = None
    
    personal_info: PersonalInfo
    
    education: Education
    
    experience: Experience

    
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
    job_metadata:Optional[JobMetadata]
    
    industry: Optional[str] = Field(
        None,
        description="Primary industry domain of the candidate based on their experience and skills (e.g., Pharmaceutical, Healthcare, Banking, Finance, Information Technology, Software Development, Manufacturing, Retail, Education, etc.)"
    )