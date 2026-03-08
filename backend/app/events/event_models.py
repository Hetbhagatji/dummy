from dataclasses import dataclass, field
from typing import Any, Optional


# ── Job lifecycle ─────────────────────────────────────────────────────────────

@dataclass
class JobStartedEvent:
    type: str
    drive_id: str
    jd_id: str
    total_resumes: int


@dataclass
class JobFailedEvent:
    type: str
    drive_id: str
    jd_id: str
    error: str


@dataclass
class JobCompletedEvent:
    type: str
    drive_id: str
    jd_id: str
    total_resumes: int


# ── JD parsing ────────────────────────────────────────────────────────────────

@dataclass
class JdParsingStartedEvent:
    type: str
    drive_id: str
    jd_id: str


@dataclass
class JdParsingCompletedEvent:
    type: str
    drive_id: str
    jd_id: str
    job_dict: dict
    job_path: str           # absolute path where job.json should be written


# ── Resume parsing ────────────────────────────────────────────────────────────

@dataclass
class ResumesParsingStartedEvent:
    type: str
    drive_id: str
    jd_id: str
    total: int


@dataclass
class ResumesParsingCompletedEvent:
    type: str
    drive_id: str
    jd_id: str
    total: int
    succeeded: int
    failed: int


@dataclass
class ResumeParsingStartedEvent:
    type: str
    drive_id: str
    jd_id: str
    resume_id: str
    index: int


@dataclass
class ResumeParsingCompletedEvent:
    type: str
    drive_id: str
    jd_id: str
    resume_id: str
    index: int
    status: str                         # "success" | "failed"
    resume_dict: Optional[dict] = None  # present on success
    resume_path: Optional[str]  = None  # where to write JSON on success
    error: Optional[str]        = None  # present on failure


# ── Matching ──────────────────────────────────────────────────────────────────

@dataclass
class ResumesMatchingStartedEvent:
    type: str
    drive_id: str
    jd_id: str
    total: int


@dataclass
class ResumesMatchingCompletedEvent:
    type: str
    drive_id: str
    jd_id: str
    total: int
    ranking: list


@dataclass
class ResumeMatchingStartedEvent:
    type: str
    drive_id: str
    jd_id: str
    resume_id: str
    index: int


@dataclass
class ResumeMatchingCompletedEvent:
    type: str
    drive_id: str
    jd_id: str
    resume_id: str
    index: int
    candidate_result: dict
    scores_path: str        # where to write scores JSON


# ── Side-effect triggers ──────────────────────────────────────────────────────

@dataclass
class SummaryUpdatedEvent:
    type: str
    summary_path: str
    summary: dict


@dataclass
class JsonFileWriteEvent:
    """Generic: write any dict to any path on disk."""
    type: str
    path: str
    data: dict
    
# ── Ranking (NEW) ─────────────────────────────────────────────────────────────

@dataclass
class ResumesRankingStartedEvent:
    type: str
    drive_id: str
    jd_id: str
    total: int          # how many matched resumes go into ranking


@dataclass
class ResumesRankingCompletedEvent:
    type: str
    drive_id: str
    jd_id: str
    total: int
    ranking: list       # final ranked list (same shape as before)