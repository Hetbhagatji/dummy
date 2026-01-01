from typing import List, Optional, Literal,Union
from pydantic import BaseModel, Field


class Skill(BaseModel):
    skill_name: str
    category: Optional[str] = None
    min_experience_years: Optional[float] = None
    proficiency_level: Optional[str] = None
    weight: Optional[float] = None


class Experience(BaseModel):
    experience_area: str
    min_years: Optional[float] = None
    max_years: Optional[float] = None


class Certification(BaseModel):
    certification_name: str
    issuing_body: Optional[str] = None


class EducationDegree(BaseModel):
    degree: str
    fields: List[str]


class SkillGroup(BaseModel):
    group_id: str
    operator: Literal["AND", "OR", "N_OF"]
    min_required: Optional[int] = None
    mandatory: bool
    skills: List[Skill] = Field(default_factory=list)
    groups: List["SkillGroup"] = Field(default_factory=list)


class ExperienceGroup(BaseModel):
    group_id: str
    operator: Literal["AND", "OR", "N_OF"]
    min_required: Optional[int] = None
    mandatory: bool
    experiences: List[Experience] = Field(default_factory=list)
    groups: List["ExperienceGroup"] = Field(default_factory=list)


class CertificationGroup(BaseModel):
    group_id: str
    operator: Literal["AND", "OR", "N_OF"]
    min_required: Optional[int] = None
    mandatory: bool
    certifications: List[Certification] = Field(default_factory=list)
    groups: List["CertificationGroup"] = Field(default_factory=list)


class EducationGroup(BaseModel):
    group_id: str
    operator: Literal["AND", "OR", "N_OF"]
    min_required: Optional[int] = None
    mandatory: bool
    degrees: List[EducationDegree] = Field(default_factory=list)
    groups: List["EducationGroup"] = Field(default_factory=list)


class JobLocation(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class JobMetadata(BaseModel):
    job_title: str
    industry: Optional[str]=None
    employment_type: Optional[Union[str, List[str]]] = None
    work_mode: Optional[Union[str, List[str]]] = None
    location: JobLocation
    experience_required_years: Optional[dict] = None
    posted_date: Optional[str] = None


class Salary(BaseModel):
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    currency: Optional[str] = None
    period: Optional[str] = None
    raw_text: Optional[str] = None


class JobSchema(BaseModel):
    job_id: Optional[str] = None
    job_metadata: JobMetadata
    education_requirements: Optional[dict] = None
    skill_requirements: Optional[dict] = None
    soft_skill_requirements: Optional[dict] = None
    certification_requirements: Optional[dict] = None
    experience_requirements: Optional[dict] = None
    responsibilities: List[str]
    salary: Optional[Salary] = None
