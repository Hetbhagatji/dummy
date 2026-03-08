from pydantic import BaseModel
from typing import List


class JDPayload(BaseModel):
    jdId: str
    fileUrl: str        # e.g. "s3://bucket/driveId/jd/jd.pdf"


class ResumeItem(BaseModel):
    resumeId: str
    fileUrl: str        # e.g. "s3://bucket/driveId/resumes/abc_resume.pdf"


class PrepareJobPayload(BaseModel):
    jd: JDPayload
    resumes: List[ResumeItem]