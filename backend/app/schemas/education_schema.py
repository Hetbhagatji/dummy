from pydantic import BaseModel, Field
from typing import List, Optional

class Education(BaseModel):
    institution: Optional[str] = Field(
        None, description="Name of college, university or school"
    )
    degree: Optional[str] = Field(
        None, description="Degree or qualification obtained"
    )
    graduation_year: Optional[str] = Field(
        None, description="Year of graduation or completion"
    )