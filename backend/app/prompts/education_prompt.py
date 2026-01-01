EDUCATION_SCHEMA = """
{
  "education_requirements": {
    "groups": [{
      "group_id": "string|null",
      "operator": "\"AND\"|\"OR\"|\"N_OF\"",
      "min_required": "int|null",
      "mandatory": "boolean",
      "degrees": [{
        "degree": "string|null",
        "fields": ["string"]|null
      }]
    }]
  }
}
"""

EDUCATION_PARSING_RULES = """
**STEP 0: DEGREE SPLITTING (MANDATORY - Process EVERY degree name FIRST)**

Group Id related rule
-group_id must be start with like edu1 then edu2,edu3

Critical
-VAGUE FIELD EXCLUSION RULE:
-Ignore and do NOT extract vague or non-specific field terms such as “related field”, “relevant field”, “equivalent discipline”, or similar placeholders; only extract explicitly named academic fields.

For ANY degree string, split using this EXACT algorithm:
1. Find FIRST occurrence of: space | "-" | "/" | "in" | "(" 
2. Everything BEFORE = degree
3. Everything AFTER (cleaned) = fields[0]

UNIVERSAL RULES:
- Take LEFT side of FIRST separator → degree
- Take RIGHT side of FIRST separator → fields[0] 
- Remove "(" ")" from fields
- If no separator → fields = null

**STEP 1: Identify Atomic Degrees**
Extract all individual degree mentions while preserving sentence position and relationships.

**STEP 2: Parse Sentence Structure for Logical Relationships**

1. **Separators and their meaning:**
   - **"or"** → alternatives (OR relationship)
   - **"/"** → alternatives (OR relationship)
   - **"and"** → cumulative (AND relationship)
   - Commas → neutral (OR unless "and" follows)

2. **Softening phrases (OR/flexibility):**
   - "or similar", "such as", "including", "like", "any of", "one of" → OR

3. **Nested structure:**
   - "A, B or C" → A AND (B OR C) → TWO groups
   - Group 1: [A] (AND)
   - Group 2: [B, C] (OR)

4. **Requirement strength:**
   - "required", "must", "essential" → mandatory: true
   - "preferred", "nice-to-have", "optional" → mandatory: false
   - Default → mandatory: true

**STEP 3: Create Groups Based on Logic**
- ONE logical relationship per group
- Different relationships → DIFFERENT groups
- Alternatives → operator: "OR", min_required: 1
- All required → operator: "AND", min_required: null
- Separate lines → separate groups

DEGREE IDENTIFICATION (LIGHTWEIGHT & UNIVERSAL):
- field(s) = subject/specialization only
- Concrete degrees ONLY (B.E, B.Tech, MCA)
- NO abstraction unless verbatim ("Bachelor's", "Master's")

FIELD INFERENCE RULE:
- Extract after: "-", "/", "in", "( )"
- No field mentioned → fields = null

NO ENFORCEMENT RULE:
- NEVER normalize/classify degree names
- Output exactly what's in RAW text

COMMON PATTERNS:
- "B.E or B.Tech" → OR group, min_required: 1
- "B.E, B.Tech in CS" → OR group + fields: ["CS"]
- "Master's preferred" → mandatory: false
- "BSc CS, MSc IT" → Group1: BSc+CS, Group2: MSc+IT
"""

from app.schemas.raw_schemas import RawJobData

def get_education_parsing_prompt(education_text) -> str:
    return f"""
You are a STRUCTURED EDUCATION PARSER.

TASK:
Extract and structure ONLY education-related requirements from raw text.

RAW EDUCATION BLOCK:
[EDUCATION]: {education_text}

{EDUCATION_PARSING_RULES}

Output MUST be SINGLE valid JSON matching this schema exactly:

{EDUCATION_SCHEMA}

Return ONLY valid JSON.
No markdown.
No explanation.
"""
