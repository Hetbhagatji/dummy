"""
Multi-Stage Job Description Parser Pipeline
Handles universal JDs across all industries with modular, focused stages.
"""


from groq import Groq
import os
from het_schema import JobExtraction
import json
import re
from typing import Dict, Any, List
from dotenv import load_dotenv
from het_schema import JobExtraction


schema = JobExtraction.model_json_schema()
schema_str = json.dumps(schema, indent=2)
load_dotenv()


class Stage1_EntityExtractor:
    def __init__(self, client: Groq):
        self.client = client

    def extract(self, job_text: str) -> Dict[str, Any]:
        schema = JobExtraction.model_json_schema()
        schema_str = json.dumps(schema, indent=2)

        prompt = f"""
        You are a STRICT JSON extraction engine.

        Your task:
        Extract factual information from the Job Description and output a SINGLE valid JSON
        that EXACTLY conforms to the following JSON Schema.

        JSON SCHEMA:
        {schema_str}

        STRICT RULES:
        - Output ONLY valid JSON
        - No markdown
        - No explanations
        - No comments
        - Do NOT infer logic or operators
        - Do NOT add extra fields
        - Use null if a value is not mentioned
        - Use empty arrays [] when applicable
        - Do NOT invent data

        Job Description:
        {job_text}
        """

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You extract structured job data strictly following a JSON schema."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        if not content:
            raise RuntimeError("LLM returned empty content in Stage 1")
        return json.loads(content)


class Stage2_RelationshipMapper:
    """
    Stage 2: Analyze relationships and create logical groups.
    Focus: Apply AND/OR/N_OF operators based on sentence structure.
    """

    def __init__(self, client: Groq):
        self.client = client

    def map_relationships(self, entities: Dict[str, Any], job_text: str) -> Dict[str, Any]:
        prompt = f"""
You are a requirement-logic normalizer.

You will convert extracted job requirements into explicit logical groups
using AND / OR / N_OF operators.

INPUT:
- Extracted entities (already identified)
- Original job text (context only)

IMPORTANT:
Logical correctness is more important than completeness.

=====================================================
GLOBAL OVERRIDE RULES (HIGHEST PRIORITY)
=====================================================

1. Preference keywords:
   ("preferred", "nice to have", "desirable", "plus", "added advantage")
   → mandatory = false

2. Comma-separated lists WITHOUT explicit AND/OR
   → default to OR, min_required = 1

3. Languages are NOT skills.
   → Never include languages inside skill groups.

4. Never use AND unless the sentence explicitly enforces joint necessity.

=====================================================
STEP 1: SENTENCE INTENT CLASSIFICATION
=====================================================

For each requirement sentence, classify intent as ONE:

A. MANDATORY_REQUIREMENT  
B. PREFERRED_REQUIREMENT  
C. OPTIONAL_INFORMATION  

Do NOT assign operators yet.

=====================================================
STEP 2: STRUCTURE CLASSIFICATION
=====================================================

Classify sentence structure as ONE:

1. PURE_OR
   Explicit alternatives only

2. PURE_AND
   Explicit joint requirement only

3. ANCHOR_WITH_OPTIONS
   One mandatory anchor + optional alternatives

4. MINIMUM_SELECTION
   Explicit numeric selection (N, at least N, any N)

If structure is ambiguous, choose PURE_OR.

=====================================================
STEP 3: GROUP CONSTRUCTION
=====================================================

- PURE_OR → OR group, min_required = 1
- PURE_AND → AND group
- ANCHOR_WITH_OPTIONS →
    Group 1: anchor (AND, mandatory)
    Group 2: options (OR, mandatory=false)
- MINIMUM_SELECTION → N_OF

=====================================================
OUTPUT RULES
=====================================================

- group_id must be sequential strings
- mandatory reflects intent classification
- Do NOT invent constraints
- Do NOT merge unrelated items
- Output ONLY valid JSON

OUTPUT FORMAT:

{
  "skill_groups": [
    {
      "group_id": "1",
      "operator": "AND | OR | N_OF",
      "min_required": null,
      "mandatory": true,
      "items": ["item1", "item2"]
    }
  ],
  "education_groups": [],
  "certification_groups": [],
  "experience_groups": []
}
"""


        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a logical relationship expert. Analyze sentence structure to determine AND/OR/N_OF relationships."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )

        content = response.choices[0].message.content.strip()
        if not content:
            raise RuntimeError("LLM returned empty content in Stage 2")

        # Strip all forms of code fences
        content = response.choices[0].message.content.strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = content.strip()

        if not content:
            raise RuntimeError("LLM returned empty content after stripping code fences in Stage 2")

        return json.loads(content)


class Stage3_SchemaAssembler:
    """
    Stage 3: Assemble final JSON according to Job schema.
    Focus: Map groups to schema, validate, and fix common errors.
    """

    def __init__(self, client: Groq):
        self.client = client

    def assemble(self, entities: Dict[str, Any], relationships: Dict[str, Any], schema: str) -> Dict[str, Any]:
        prompt = f"""You are a JSON schema assembler. Convert extracted data into the exact schema format.

        SCHEMA:
        {schema}

        EXTRACTED ENTITIES:
        {json.dumps(entities, indent=2)}

        LOGICAL GROUPS:
        {json.dumps(relationships, indent=2)}

        YOUR TASK:
        1. Map entities and groups to the exact schema structure
        2. Create proper skill_requirements with groups containing SkillRequirement objects
        3. Create proper education_requirements, certification_requirements, experience_requirements
        4. Ensure all group_id values are sequential strings: "1", "2", "3", etc.
        5. Set proper categories for skills (Programming Language, Framework, Tool, Database, API, etc.)
        6. Validate mandatory flags align with requirement language
        7. Use null for missing optional fields
        8. Use [] for empty arrays

        CRITICAL MAPPING RULES:
        - Each skill group contains a "skills" array with objects having: skill_name, category, min_experience_years, proficiency_level, weight
        - Each education group contains a "degrees" array with objects having: degree, fields
        - Each experience group contains an "experiences" array with objects having: experience_area, min_years, max_years
        - Soft skills are a simple array under soft_skill_requirements.skills

        OUTPUT:
        Return ONLY valid JSON matching the Job schema exactly. NO markdown, NO explanations.

        The final JSON should be production-ready and pass schema validation."""

        response = self.client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a schema validation expert. Ensure perfect compliance with the target schema."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        content = response.choices[0].message.content.strip()
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = content.strip()

        if not content:
            raise RuntimeError("LLM returned empty content in Stage 3")

        return json.loads(content)


class JobParserPipeline:
    """
    Main pipeline orchestrator.
    Coordinates all 3 stages and handles errors.
    """

    def __init__(self, api_key: str = None):
        if api_key is None:
            api_key = os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=api_key)
        self.stage1 = Stage1_EntityExtractor(self.client)
        self.stage2 = Stage2_RelationshipMapper(self.client)
        self.stage3 = Stage3_SchemaAssembler(self.client)

    def parse(self, job_text: str, job_schema: str) -> Dict[str, Any]:
        """
        Execute full 3-stage pipeline.

        Args:
            job_text: Raw job description text
            job_schema: JSON schema string from Job.schema_json()

        Returns:
            Validated JSON matching Job schema
        """
        try:
            print("🔍 Stage 1: Extracting entities...")
            entities = self.stage1.extract(job_text)
            print(f"   ✓ Extracted {len(entities.get('skills', []))} skills, "
                  f"{len(entities.get('degrees', []))} degrees, "
                  f"{len(entities.get('certifications', []))} certifications")

            print("\n🔗 Stage 2: Mapping relationships...")
            relationships = self.stage2.map_relationships(entities, job_text)
            print(f"   ✓ Created {len(relationships.get('skill_groups', []))} skill groups")

            print("\n📦 Stage 3: Assembling final JSON...")
            final_json = self.stage3.assemble(entities, relationships, job_schema)
            print("   ✓ Schema validation complete")

            return final_json

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            raise
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            raise


# Usage Example
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = JobParserPipeline()

    # Example job description
    job_text = """
    Responsibilities:

*	Conduct quality checks on equipment performance

*	Ensure compliance with industry standards

*	Collaborate with cross-functional teams

*	Prepare quotes accurately

*	Execute detail engineering tasks


Role: Production & Manufacturing - Other

Industry Type: Aviation
 
Department: Production, Manufacturing & Engineering

Employment Type: Full Time, Permanent

Role Category: Production & Manufacturing - Other

Education


UG: B.Tech/B.E. in Aviation, Mechanical, Diploma in Mechatronics

Key Skills


Detail Engineering are preferred key skill. Communication Skills, English,Telugu, Documentation,
Quality Check, Quote Preparation, Hindi, Quality Assurance

    """

    # Get schema (in real usage, import from job_schema.py)
    from app.schemas.job_schema import Job
    schema = json.dumps(Job.model_json_schema(), indent=2)

    # Parse
    result = pipeline.parse(job_text, schema)

    # Output
    print("\n" + "="*60)
    print("FINAL OUTPUT:")
    print("="*60)
    print(json.dumps(result, indent=2))
