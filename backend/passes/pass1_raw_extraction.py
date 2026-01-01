def get_pass1_prompt(job_text: str) -> str:
    return f"""
You are a job description information extractor.

Your task is to extract RAW FACTS ONLY from the job description.

====================================================
CRITICAL OUTPUT RULES
====================================================
- Output ONLY valid JSON
- No explanations
- No schema nesting beyond what is asked
- Preserve original wording exactly
- Do NOT infer meaning
- Do NOT apply AND / OR logic
- Do NOT group items logically
- Do NOT mark mandatory or optional

====================================================
WHAT TO EXTRACT
====================================================
From each sentence or bullet, extract atomic items:

- Skills, tools, technologies, frameworks, languages
- Experience areas and durations
- Degrees and education fields
- Certifications
- Job metadata (job type, location, work mode)
- Salary expressions
- Responsibilities

Each extracted item MUST:
- Belong to exactly one sentence
- Preserve original text form

====================================================
JOB DESCRIPTION
====================================================
{job_text}

====================================================
OUTPUT FORMAT
====================================================
Return a JSON object with:
- sentences[]
  - sentence_id
  - raw_text
  - items[] with:
    - text
    - type
    - sentence_id
    - span_hint (if helpful, otherwise null)
"""
