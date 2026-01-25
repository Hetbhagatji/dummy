from pydantic import BaseModel, Field
from typing import Optional,List
from app.schemas.resume_schema.location import Location
class EducationEntry(BaseModel):
    degree_level:Optional[str]=None
    degree_name: Optional[str] = Field(
        None,
        description="Universal degree levels: Bachelor's, Master's, PhD, MD, PharmD, MBA, JD, Diploma, etc."
    )
    field: Optional[List[str]] = Field(
        None,
        description="Field for ANY industry: Computer Science, Pharmacy, Finance, Medicine, Law, Mechanical Engineering, etc."
    )
    institution: Optional[str] = None    
    location: Optional[Location] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = Field(
        None,
        description="Graduation date or 'Present' if ongoing"
    )
    grade: Optional[str] = Field(
        None,
        description="CGPA, Percentage, GPA, Grade, or Honors"
    )
    achievements: Optional[List[str]] = Field(
        default_factory=list,
        description="Academic honors, awards, research, publications"
    )


class Education(BaseModel):
    entries: List[EducationEntry] = Field(
        default_factory=list,
        description="All educational qualifications"
    )
