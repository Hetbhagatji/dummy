from typing import Optional,List
from pydantic import BaseModel
from app.schemas.resume_schema.location import Location
class JobMetadata(BaseModel):
    job_title: Optional[str]=None
    industry: Optional[str]=None
    employment_type: Optional[str]
    work_mode: Optional[str]
    