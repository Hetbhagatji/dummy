# ── Job lifecycle ─────────────────────────────────────────────────────────────
JOB_STARTED   = "JOB_STARTED"
JOB_FAILED    = "JOB_FAILED"
JOB_COMPLETED = "JOB_COMPLETED"

# ── JD parsing ────────────────────────────────────────────────────────────────
JD_PARSING_STARTED   = "JD_PARSING_STARTED"
JD_PARSING_COMPLETED = "JD_PARSING_COMPLETED"

# ── Resume parsing ────────────────────────────────────────────────────────────
RESUMES_PARSING_STARTED   = "RESUMES_PARSING_STARTED"
RESUMES_PARSING_COMPLETED = "RESUMES_PARSING_COMPLETED"
RESUME_PARSING_STARTED    = "RESUME_PARSING_STARTED"
RESUME_PARSING_COMPLETED  = "RESUME_PARSING_COMPLETED"

# ── Matching ──────────────────────────────────────────────────────────────────
RESUMES_MATCHING_STARTED   = "RESUMES_MATCHING_STARTED"
RESUMES_MATCHING_COMPLETED = "RESUMES_MATCHING_COMPLETED"
RESUME_MATCHING_STARTED    = "RESUME_MATCHING_STARTED"
RESUME_MATCHING_COMPLETED  = "RESUME_MATCHING_COMPLETED"

# ── Ranking (NEW) ─────────────────────────────────────────────────────────────
RESUMES_RANKING_STARTED    = "RESUMES_RANKING_STARTED"   # ← NEW
RESUMES_RANKING_COMPLETED  = "RESUMES_RANKING_COMPLETED" # ← NEW

# ── Side-effect triggers ──────────────────────────────────────────────────────
SUMMARY_UPDATED   = "SUMMARY_UPDATED"
JSON_FILE_WRITE   = "JSON_FILE_WRITE"   # generic: write any JSON to disk

# ── Debug timing ──────────────────────────────────────────────────────────────
TIMING_EVENT = "TIMING_EVENT"