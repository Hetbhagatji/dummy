from pydantic import BaseModel, Field
from typing import Optional,List
class Skill(BaseModel):
    skill_name: str = Field(
        ...,
        description="Skill for ANY industry: Python, Clinical Research, Financial Analysis, Drug Formulation, Legal Research, etc."
    )
    category: Optional[str] = Field(
        None,
        description="""Flexible categories based on industry:
        - IT: Programming Language, Framework, Database, DevOps, Cloud
        - Healthcare: Clinical Skills, Laboratory Skills, Patient Care, Medical Procedures
        - Pharma: Drug Development, Regulatory Affairs, Quality Control, Clinical Trials
        - Finance: Financial Analysis, Trading, Risk Management, Compliance
        - Legal: Legal Research, Contract Law, Litigation, Intellectual Property
        - Manufacturing: Production, Quality Assurance, Supply Chain
        - General: Soft Skills, Communication, Leadership, Project Management
        """
    )
    years_of_experience: Optional[float] = Field(
        None,
        description="Years of experience with this specific skill"
    )
    


class Skills(BaseModel):
    skills: List[Skill] = Field(
        default_factory=list,
        description="Domain-specific technical skills for any industry"
    )
    soft_skills: Optional[List[str]] = Field(
        default_factory=list,
        description="Communication, Leadership, Problem-solving, Teamwork, etc."
    )
