from app.schemas.job_schema import Job

def get_job_prompt(job_text: str) -> str:
    schema = Job.schema_json(indent=2)

    return f"""
You are an expert job description parser. Your task is to extract structured information from any job description
and convert it into a valid JSON object that strictly follows the provided schema.

==================================================================
OUTPUT FORMAT (CRITICAL)
==================================================================
- Return ONLY valid JSON starting with {{ and ending with }}
- NO markdown code blocks, NO explanations, NO comments
- Use null for missing values
- Use [] for empty arrays
- Ensure all JSON is properly escaped and valid
- group_id must be sequential strings: "1", "2", "3", etc. (never null)

**Schema:**
{schema}

**Job Description:**
{job_text}
==================================================================
EXTRACTION PROCESS (CRITICAL - READ CAREFULLY)
==================================================================

**STEP 1: Identify Atomic Items**
Extract all individual items mentioned:
- Skills, tools, technologies, frameworks, languages
- Degrees, fields of study, qualifications
- Certifications, licenses
- Experience areas, domains, specializations

Identify atomic items WHILE preserving their sentence position,
governing terms, and dependency relationships.


**STEP 2: Parse Sentence Structure for Logical Relationships**

For each sentence or requirement, identify the logical structure by analyzing:

1. **Separators and their meaning:**
   - **"or"** → items are alternatives (OR relationship)
   - **"/"** → items are alternatives (OR relationship)
   - **"and"** → items are cumulative (AND relationship)
   - Commas are neutral separators.
      They do NOT define logical relationships by themselves.
      Logical meaning is determined ONLY by conjunctions (and, or, /) and modifiers.


2. **Softening phrases (indicate OR/flexibility):**
   - "or similar", "such as", "including", "like", "any of", "one of"
   - These phrases mean alternatives are acceptable

3. **Nested structure pattern:**
   When you see: "A, B or C"
   - This means: A is separate from the choice between B and C
   - Structure: A AND (B OR C)
   - Create TWO groups:
     - Group 1: A (standalone)
     - Group 2: B, C (alternatives)

4. **Multiple independent items in one sentence:**
   When items are separated by different logical connectors:
   - Split into separate groups based on actual relationships
   - Example: "X / Y, Z, and W" → Group 1: (X OR Y), Group 2: Z, Group 3: W

5. **Requirement strength indicators:**
   - "required", "must", "essential", "mandatory" → mandatory: true
   - "preferred", "nice-to-have", "plus", "good to have", "optional" → mandatory: false
   - If not specified → assume mandatory: true for core requirements

6. Anchoring rule:
   If a requirement mentions a primary concept followed by
   implementation choices or variations, the primary concept
   is mandatory and the variations are alternatives.

**STEP 3: Create Groups Based on Parsed Logic**

Only after understanding the sentence structure, create groups:
- A group must represent ONE and only ONE logical relationship.
   If an item does not share the same governing connector,
   it MUST be placed in a separate group.

- Items with DIFFERENT relationships go in DIFFERENT groups
- Never flatten complex logic into a single group

==================================================================
COMMON PATTERNS TO RECOGNIZE
==================================================================

**Pattern 1: Common item + alternatives**
Text: "A, B or C"
Logic: A AND (B OR C)
Groups: 
- Group 1: [A] with AND
- Group 2: [B, C] with OR

**Pattern 2: Slash as alternatives**
Text: "X / Y"
Logic: X OR Y
Groups:
- Group 1: [X, Y] with OR

**Pattern 3: Multiple independent items with different connectors**
Text: "X / Y, Z, and W"
Logic: (X OR Y) AND Z AND W
Groups:
- Group 1: [X, Y] with OR
- Group 2: [Z] with AND
- Group 3: [W] with AND

**Pattern 4: Softening phrases**
Text: "A, B, or similar"
Logic: A OR B (any one acceptable)
Groups:
- Group 1: [A, B] with OR, min_required: 1

**Pattern 5: Lists with explicit "and"**
Text: "A, B, and C"
Logic: All required together
Groups:
- Group 1: [A, B, C] with AND

==================================================================
FIELD EXTRACTION GUIDELINES
==================================================================

**job_metadata:**
- job_title, industry, employment_type, work_mode, location
- experience_required_years: min and max (e.g., "3-5 years" → min: 3, max: 5)

**education_requirements:**
- Extract degree level and fields
- Apply logical grouping rules
- Set mandatory based on requirement strength

**skill_requirements:**
- Categorize appropriately (Programming Language, Framework, API, Database, Tool, etc.)
- Extract experience years if mentioned for specific skills
- Apply logical grouping rules - CRITICAL: respect sentence structure
- Never merge items with different logical relationships

**soft_skill_requirements:**
- Extract interpersonal, behavioral, communication skills
- Simple list, no complex grouping needed

**certification_requirements:**
- Extract certifications and issuing bodies
- Apply logical grouping if multiple certifications mentioned
- Set mandatory based on requirement strength

**experience_requirements:**
- Extract specific experience areas/domains
- Include years if specified
- Apply logical grouping rules

**responsibilities:**
- Extract job duties as list items

**salary:**
- Extract min, max, currency, period
- Preserve original in raw_text


==================================================================
CRITICAL REMINDERS
==================================================================
- Commas DO NOT always mean AND - analyze context
- "/" and "or" ALWAYS mean OR
- Split nested logic - never flatten into one group
- Create separate groups when items have different relationships
- Use null for missing information
- Output ONLY valid JSON

**Output:**
"""
