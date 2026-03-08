from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime

OperatorType = Literal["AND", "OR", "N_OF"]

# BASIC SHARED STRUCTURES
class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class ExperienceRange(BaseModel):
    min: Optional[int] = Field(None, description="Minimum years of experience required")
    max: Optional[int] = Field(None, description="Maximum years of experience allowed")

# ORGANIZATION DETAILS
class Organization(BaseModel):
    company_name: Optional[str] = None
    company_type: Optional[str] = Field(None, description="Product-based, Service-based, Startup, Enterprise")
    company_size: Optional[str] = Field(None, description="Employee count range such as 50-100, 100-500")

# ROLE & JOB METADATA
class JobMetadata(BaseModel):
    job_title: Optional[str] = Field(..., description="Official job title such as Senior Software Engineer")
    industry: Optional[str] = Field(..., description="Industry domain such as IT, Pharmaceutical, Banking")
    employment_type: Optional[str] = Field(None, description="Full-time, Part-time, Contract, Internship")
    work_mode: Optional[str] = Field(None, description="Onsite, Remote, Hybrid")
    location: Optional[List[Location]] = None
    experience_required_years: Optional[ExperienceRange] = None
    posted_date: Optional[str] = None

class SalaryRange(BaseModel):
    min_amount: Optional[float] = Field(None, description="Minimum salary amount")
    max_amount: Optional[float] = Field(None, description="Maximum salary amount")
    currency: Optional[str] = Field(None, description="Currency code such as INR, USD")
    period: Optional[str] = Field(None, description="Salary period: yearly, monthly, hourly")
    raw_text: Optional[str] = Field(None, description="Original salary text as mentioned in JD")

class RoleDetails(BaseModel):
    summary: Optional[str] = Field(None, description="High-level role summary used for semantic matching")
    seniority_level: Optional[str] = Field(None, description="Junior, Mid, Senior, Lead")
    team: Optional[str] = Field(None, description="Team or specialization such as Backend Engineering")

# EDUCATION REQUIREMENTS
class DegreeRequirement(BaseModel):
    degree_level:Optional[str]=None
    degree_name:Optional[str]=None
    fields: Optional[List[str]] = None

class EducationGroup(BaseModel):
    group_id: Optional[str] = None
    operator: OperatorType
    min_required: Optional[int] = None
    mandatory: bool = True
    degrees: List[DegreeRequirement]

class EducationRequirements(BaseModel):
    groups: List[EducationGroup]

# CERTIFICATIONS
class CertificationRequirement(BaseModel):
    certification_name: Optional[str]
    issuing_body: Optional[str] = None

class CertificationGroup(BaseModel):
    group_id: Optional[str] = None
    operator: OperatorType
    min_required: Optional[int] = None
    mandatory: bool = True
    certifications: List[CertificationRequirement]

class CertificationRequirements(BaseModel):
    groups: Optional[List[CertificationGroup]]

# SKILL REQUIREMENTS
class SkillRequirement(BaseModel):
    skill_name: str
    category: Optional[str] = Field(None, description="Programming Language, Framework, DevOps, Database")
    
class SkillGroup(BaseModel):
    group_id: Optional[str] = None
    operator: Literal["AND", "OR", "N_OF"]
    min_required: Optional[int] = None
    mandatory: bool = Field(True, description="If true, failure leads to rejection")
    skills: List[SkillRequirement]

class SkillRequirements(BaseModel):
    groups: List[SkillGroup]

class SoftSkillRequirements(BaseModel):
    skills: List[str] = Field(..., description="Non-technical skills such as communication, negotiation, teamwork")

# EXPERIENCE
class ExperienceRequirement(BaseModel):
    experience_area: Optional[str] = Field(None, description="Area or context of experience such as Clinical Dentistry, Banking, Backend Development")
    min_years: Optional[float] = None
    max_years: Optional[float] = None
    key_technologies: Optional[List[str]] = None

class ExperienceGroup(BaseModel):
    group_id: Optional[str] = None
    operator: OperatorType
    min_required: Optional[int] = None
    mandatory: bool = True
    experiences: List[ExperienceRequirement]

class ExperienceRequirements(BaseModel):
    groups: List[ExperienceGroup]

# MATCHING PREFERENCES
class MatchingPreferences(BaseModel):
    skill_match_weight: float = Field(0.5)
    experience_match_weight: float = Field(0.25)
    education_match_weight: float = Field(0.15)
    location_match_weight: float = Field(0.5)
    responsibility_match_weight: float = Field(0.5)

# JOB ROOT MODEL
class Job(BaseModel):
    job_id: Optional[str] = None
    job_metadata: JobMetadata
    education_requirements: Optional[EducationRequirements] = None
    skill_requirements: Optional[SkillRequirements] = None
    soft_skill_requirements: Optional[SoftSkillRequirements] = None
    certification_requirements: Optional[CertificationRequirements] = None
    experience_requirements: Optional[ExperienceRequirements] = None
    responsibilities: Optional[List[str]] = Field(None, description="Explicit responsibilities list used for role similarity")
    salary: Optional[SalaryRange] = None

# Default values (sums to 1.0)
class MatchingPreferences(BaseModel):
    skill_match_weight: float = Field(0.5,  ge=0.0, le=1.0)    # Skills most important
    experience_match_weight: float = Field(0.25, ge=0.0, le=1.0)
    education_match_weight: float = Field(0.15, ge=0.0, le=1.0)
    location_match_weight: float = Field(0.10, ge=0.0, le=1.0)
