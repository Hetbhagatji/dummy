from pydantic import BaseModel
from typing import List, Optional

class Job(BaseModel):
    job_role: Optional[str] = None
    job_overview: Optional[str] = None
    experience_required: Optional[str] = None
    job_location: Optional[str] = None
    responsibilities: Optional[List[str]] = []
    skills_required: Optional[List[str]] = []
