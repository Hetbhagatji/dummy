from pydantic import BaseModel
from typing import List
from app.schemas.resume_schemaa import Resume
from app.schemas.job_schema import Job
from app.schemas.weight_schema import WeightSchema
class ResumeRankRequest(BaseModel):
    job: Job
    resumes: List[Resume]
    weights: WeightSchema
