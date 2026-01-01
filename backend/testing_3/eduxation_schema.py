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
