from pydantic import BaseModel, Field
from typing import List, Optional
from app.schemas.education_schema import Education
from app.schemas.experience_schema import Experience

class Resume(BaseModel):
    name: Optional[str] = Field(
        ..., description="Full name of the person"
    )
    email: Optional[str] = Field(
        None, description="Email address of the person"
    )
    contact_number: Optional[str] = Field(
        None, description="Phone number of the person"
    )
    experience: Optional[List[Experience]] = Field(
        None, description="List of work experiences"
    )
    education: Optional[List[Education]] = Field(
        None, description="List of educational qualifications"
    )