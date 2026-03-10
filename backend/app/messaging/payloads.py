# messaging/payloads.py

def job_started(job_id: str, jd_id: str, total_resumes: int) -> dict:
    return {
        "jobId":        job_id,
        "jdId":         jd_id,
        "totalResumes": total_resumes,
    }

# ── JD ────────────────────────────────────────────────────────────────────────

def jd_parsing_started(job_id: str, jd_id: str) -> dict:
    return {
        "jobId": job_id,
        "jdId":  jd_id,
    }

def jd_parsing_completed(job_id: str, jd_id: str, parsed_job: dict) -> dict:
    return {
        "jobId":     job_id,
        "jdId":      jd_id,
        "parsedJob": parsed_job,
    }

# ── Resume parsing ────────────────────────────────────────────────────────────

def resumes_parsing_started(job_id: str, jd_id: str, total: int) -> dict:
    return {
        "jobId": job_id,
        "jdId":  jd_id,
        "total": total,
    }

def resume_parsing_started(job_id: str, jd_id: str, resume_id: str, index: int) -> dict:
    return {
        "jobId":    job_id,
        "jdId":     jd_id,
        "resumeId": resume_id,
        "index":    index,
    }

def resume_parsing_completed(
    job_id: str,
    jd_id: str,
    resume_id: str,
    index: int,
    status: str,
    parsed_resume: dict = None,
    error: str = None,
) -> dict:
    payload = {
        "jobId":    job_id,
        "jdId":     jd_id,
        "resumeId": resume_id,
        "index":    index,
        "status":   status,
    }
    if status == "success" and parsed_resume:
        payload["parsedResume"] = parsed_resume
    if status == "failed" and error:
        payload["error"] = error
    return payload

def resumes_parsing_completed(
    job_id: str, jd_id: str,
    total: int, succeeded: int, failed: int
) -> dict:
    return {
        "jobId":     job_id,
        "jdId":      jd_id,
        "total":     total,
        "succeeded": succeeded,
        "failed":    failed,
    }

# ── Resume matching ───────────────────────────────────────────────────────────

def resumes_matching_started(job_id: str, jd_id: str, total: int) -> dict:
    return {
        "jobId": job_id,
        "jdId":  jd_id,
        "total": total,
    }

def resume_matching_started(
    job_id: str, jd_id: str, resume_id: str, index: int
) -> dict:
    return {
        "jobId":    job_id,
        "jdId":     jd_id,
        "resumeId": resume_id,
        "index":    index,
    }

# ✅ FIX in payloads.py
def resume_matching_completed(
    job_id: str,
    jd_id: str,
    resume_id: str,
    index: int,
    status: str,
    candidate_result: dict = None,
    error: str = None,
) -> dict:
    payload = {
        "jobId":    job_id,
        "jdId":     jd_id,
        "resumeId": resume_id,
        "index":    index,
        "status":   status,
    }
    if status == "success" and candidate_result:
        payload["candidateResult"] = candidate_result
    if status == "failed" and error:
        payload["error"] = error
    return payload

def resumes_matching_completed(
    job_id: str, jd_id: str,
    total: int, succeeded: int, failed: int   # ← drop ranking, add counts
) -> dict:
    return {
        "jobId":     job_id,
        "jdId":      jd_id,
        "total":     total,
        "succeeded": succeeded,
        "failed":    failed,
    }

# ── Final ─────────────────────────────────────────────────────────────────────

def job_completed(job_id: str, jd_id: str, total_resumes: int) -> dict:
    return {
        "jobId":        job_id,
        "jdId":         jd_id,
        "totalResumes": total_resumes,
    }

def job_failed(job_id: str, jd_id: str, error: str) -> dict:
    return {
        "jobId": job_id,
        "jdId":  jd_id,
        "error": error,
    }
    
# ── Ranking (NEW) ─────────────────────────────────────────────────────────────

def resumes_ranking_started(job_id: str, jd_id: str, total: int) -> dict:
    return {
        "jobId": job_id,
        "jdId":  jd_id,
        "total": total,
    }

def resumes_ranking_completed(
    job_id: str, jd_id: str,
    total: int, ranking: list
) -> dict:
    return {
        "jobId":   job_id,
        "jdId":    jd_id,
        "total":   total,
        "ranking": ranking,
    }