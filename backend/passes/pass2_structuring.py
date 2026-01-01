from job_schema import Job

def get_pass2_prompt(raw_json: str) -> str:
    schema = Job.schema_json(indent=2)

    return f"""
You are a job description STRUCTURING engine.

You will receive RAW extracted data.
Your task is to interpret logical relationships and produce
a final JSON strictly following the provided schema.

====================================================
ABSOLUTE RULES
====================================================
- Output ONLY valid JSON
- Must strictly conform to the schema
- group_id must be sequential strings: "1", "2", "3", ...
- Never invent items not present in raw input
- Never flatten different logical relationships
- Commas alone DO NOT imply AND or OR

====================================================
LOGICAL INTERPRETATION RULES
====================================================

1. OR indicators:
   - "or"
   - "/"
   - "one of", "any of", "either"

2. AND indicators:
   - "and"
   - explicit requirement lists

3. Anchoring rule:
   If a primary concept is followed by alternatives,
   the primary concept is mandatory,
   alternatives form an OR group.

4. Sentence boundary rule:
   Items from different sentences must NOT be merged
   unless logic explicitly connects them.

5. Mixed connectors:
   If items do not share the same governing connector,
   they MUST be split into separate groups.

====================================================
SCHEMA
====================================================
{schema}

====================================================
RAW INPUT
====================================================
{raw_json}

====================================================
OUTPUT
====================================================
Return the final structured Job JSON.
"""
