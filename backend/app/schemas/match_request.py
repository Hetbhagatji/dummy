from app.schemas.job_schema import Job
from app.schemas.resume_schema.resume_schema import Resume
from app.schemas.matching_preferences import MatchingPreferences
from pydantic import BaseModel
class MatchRequest(BaseModel):
    resume: Resume
    job: Job
    prefs: MatchingPreferences
