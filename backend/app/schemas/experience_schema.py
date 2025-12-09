from pydantic import BaseModel,Field
from typing import Optional

class Experience(BaseModel):
    company_name: Optional[str] = Field(
        None, description="Name of the company where the person worked"
    )
    role: Optional[str] = Field(
        None, description="Job title or	role in the company"
    )
    duration: Optional[str] = Field(
        None, description="Duration of employment (example: Jan 2020 - Mar 2022)"
    )
    description: Optional[str] = Field(
        None, description="Summary of responsibilities and work done"
    )