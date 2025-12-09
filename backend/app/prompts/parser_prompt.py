from app.schemas.resume_schema import Resume

def get_resume_prompt(resume_text: str) -> str:
    schema = Resume.schema_json(indent=2)
    
    return f"""Extract structured information from the resume and return it as JSON.

CRITICAL INSTRUCTIONS:
1. Return ONLY a valid JSON object - no markdown code blocks, no explanations
2. Do not wrap the JSON in ```json``` or any other formatting
3. Start your response with {{ and end with }}
4. Follow this exact schema:

{schema}

FIELD EXTRACTION RULES:
- Extract data exactly as it appears in the resume
- For missing fields, use null (not "null" string, not empty string)
- For arrays/lists, use [] if no items found
- Ensure all strings are properly escaped
- Format dates as strings in ISO format (YYYY-MM-DD) or as written
- For phone numbers and emails, extract exact text without modification

VALIDATION:
- Double-check the JSON is valid before responding
- Ensure all required fields from schema are present
- Match data types exactly (string, number, array, object, boolean, null)

Resume text to parse:
---
{resume_text}
---

Respond with JSON only:"""