from pydantic import BaseModel, Field
from typing import List, Optional


# ---------------------------
# BASIC STRUCTURES
# ---------------------------

class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class ExperienceRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None


class SalaryRange(BaseModel):
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    raw_text: Optional[str] = None


# ---------------------------
# JOB METADATA
# ---------------------------

class JobMetadata(BaseModel):
    job_title: Optional[str] = None
    industry: Optional[str] = None
    employment_type: Optional[str] = None
    work_mode: Optional[str] = None
    location: Optional[Location] = None
    posted_date: Optional[str] = None


# ---------------------------
# EDUCATION
# ---------------------------

class EducationRequirement(BaseModel):
    degree: Optional[List[str]] = None          # Bachelor's, Master's, PhD
    fields: Optional[List[str]] = None    # Computer Science, Civil, etc.


class EducationRequirements(BaseModel):
    items: List[EducationRequirement]


# ---------------------------
# SKILLS
# ---------------------------

class Skill(BaseModel):
    name: str
    category: Optional[str] = None        # Programming Language, Tool, Framework


class SkillRequirements(BaseModel):
    items: List[Skill]


# ---------------------------
# CERTIFICATIONS
# ---------------------------

class Certification(BaseModel):
    name: Optional[str]=None
    issuing_body: Optional[str] = None


class CertificationRequirements(BaseModel):
    items: List[Certification]


# ---------------------------
# EXPERIENCE
# ---------------------------

class ExperienceRequirement(BaseModel):
    area: Optional[str] = None
    years: Optional[ExperienceRange] = None


class ExperienceRequirements(BaseModel):
    items: List[ExperienceRequirement]


# ---------------------------
# SOFT SKILLS
# ---------------------------

class SoftSkillRequirements(BaseModel):
    skills: List[str]


# ---------------------------
# ROOT JOB MODEL
# ---------------------------

class JobExtraction(BaseModel):
    job_id: Optional[str] = None

    job_metadata: Optional[JobMetadata] = None

    education_requirements: Optional[EducationRequirements] = None
    skill_requirements: Optional[SkillRequirements] = None
    soft_skill_requirements: Optional[SoftSkillRequirements] = None
    certification_requirements: Optional[CertificationRequirements] = None
    experience_requirements: Optional[ExperienceRequirements] = None

    responsibilities: Optional[List[str]] = None

    salary: Optional[SalaryRange] = None
