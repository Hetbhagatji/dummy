from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
from datetime import date


# ---------------------------
# PERSONAL INFORMATION
# ---------------------------

class ContactInformation(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    location: Optional[str] = Field(
        None,
        description="City, State, Country format"
    )


class PersonalInfo(BaseModel):
    full_name: Optional[str] = None
    contact: Optional[ContactInformation] = None
    professional_summary: Optional[str] = Field(
        None,
        description="Brief professional summary or objective"
    )


# ---------------------------
# EDUCATION
# ---------------------------

class EducationEntry(BaseModel):
    degree: Optional[str] = Field(
        None,
        description="Degree level: Bachelor's, Master's, PhD, Diploma"
    )
    field_of_study: Optional[str] = Field(
        None,
        description="Specialization such as Computer Science, Pharmacy"
    )
    institution: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = Field(
        None,
        description="Graduation date or 'Present' if ongoing"
    )
    grade: Optional[str] = Field(
        None,
        description="CGPA, Percentage, or Grade"
    )
    achievements: Optional[List[str]] = Field(
        default_factory=list,
        description="Academic honors, awards, publications"
    )


class Education(BaseModel):
    entries: List[EducationEntry] = Field(
        default_factory=list,
        description="List of all educational qualifications"
    )


# ---------------------------
# WORK EXPERIENCE
# ---------------------------

class WorkExperience(BaseModel):
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = Field(
        None,
        description="Full-time, Part-time, Contract, Internship"
    )
    start_date: Optional[str] = None
    end_date: Optional[str] = Field(
        None,
        description="End date or 'Present' if current"
    )
    duration_months: Optional[int] = Field(
        None,
        description="Total duration in months"
    )
    responsibilities: Optional[List[str]] = Field(
        default_factory=list,
        description="Key responsibilities and achievements"
    )
    technologies_used: Optional[List[str]] = Field(
        default_factory=list,
        description="Technologies, tools, frameworks used"
    )


class WorkHistory(BaseModel):
    entries: List[WorkExperience] = Field(
        default_factory=list
    )
    total_experience_months: Optional[int] = Field(
        None,
        description="Calculated total work experience in months"
    )
    total_experience_years: Optional[float] = Field(
        None,
        description="Total experience in years (rounded to 1 decimal)"
    )


# ---------------------------
# SKILLS
# ---------------------------

class Skill(BaseModel):
    skill_name: str
    category: Optional[str] = Field(
        None,
        description="Programming Language, Framework, Database, DevOps, Soft Skill"
    )
    proficiency_level: Optional[str] = Field(
        None,
        description="Beginner, Intermediate, Advanced, Expert"
    )
    years_of_experience: Optional[float] = Field(
        None,
        description="Years of experience with this skill"
    )
    last_used: Optional[str] = Field(
        None,
        description="When the skill was last used (year or 'Current')"
    )


class Skills(BaseModel):
    technical_skills: List[Skill] = Field(
        default_factory=list,
        description="All technical skills"
    )
    soft_skills: Optional[List[str]] = Field(
        default_factory=list,
        description="Communication, Leadership, Problem-solving, etc."
    )


# ---------------------------
# CERTIFICATIONS
# ---------------------------

class Certification(BaseModel):
    certification_name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = Field(
        None,
        description="Expiry date or null if lifetime"
    )
    credential_id: Optional[str] = None
    credential_url: Optional[str] = None


class Certifications(BaseModel):
    entries: List[Certification] = Field(
        default_factory=list
    )



# ---------------------------
# RESUME ROOT MODEL
# ---------------------------

class Resume(BaseModel):
    resume_id: Optional[str] = None
    
    personal_info: PersonalInfo
    
    education: Education
    
    work_history: WorkHistory
    
    skills: Skills
    
    # projects: Optional[Projects] = None
    
    certifications: Optional[Certifications] = None
    
    
    raw_text: Optional[str] = Field(
        None,
        description="Original resume text for reference"
    )
    
    parsed_date: Optional[str] = Field(
        None,
        description="When this resume was parsed"
    )