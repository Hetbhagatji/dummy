from pydantic import BaseModel, Field
from typing import List, Optional

class Job(BaseModel):
    job_role: Optional[str] = Field(
        None,
        description="Job title or role name such as Clinical Pharmacist, Data Analyst, Research Associate"
    )

    job_overview: Optional[str] = Field(
        None,
        description="Detailed textual description of the job including responsibilities, expectations, and role summary"
    )

    experience_required: Optional[str] = Field(
        None,
        description="Required or preferred years of professional experience for the job"
    )

    job_location: Optional[str] = Field(
        None,
        description="Location of the job including city, state, or country"
    )

    responsibilities: Optional[List[str]] = Field(
        None,
        description="List of key job responsibilities and daily tasks"
    )

    skills_required: Optional[List[str]] = Field(
        None,
        description="List of technical and soft skills required or preferred for the role"
    )

    job_type: Optional[str] = Field(
        None,
        description="Type of employment such as full-time, part-time, contract, or internship"
    )

    certifications_required: Optional[str] = Field(
        None,
        description="Professional certifications or licenses required or preferred for the job"
    )

    education_required: Optional[List[str]] = Field(
        None,
        description="Minimum educational qualification required for the role"
    )

    estimated_salary: Optional[str] = Field(
        None,
        description="Salary text extracted exactly as written (e.g. ₹6–10 LPA, ₹80,000 per month)"
    )

    salary_period: Optional[str] = Field(
        None,
        description="Salary period. Must be one of: 'yearly', 'monthly', 'hourly'"
    )

    company_domain: Optional[str] = Field(
        None,
        description=(
            "Primary industry domain of the company such as Pharmaceutical, Banking, "
            "Healthcare, IT, Manufacturing, Education, FinTech, etc."
        )
    )

    job_domain: Optional[str] = Field(
        None,
        description=(
            "Functional domain of the job role such as Data Analytics, Software Engineering, "
            "Clinical Research, Regulatory Affairs, Sales, Marketing, Finance, HR, etc."
        )
    )
