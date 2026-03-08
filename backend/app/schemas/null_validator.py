# app/schemas/null_validator.py
from pydantic import field_validator

NULL_STRINGS = {"null", "none", "n/a", ""}

class NullSafeValidator:
    """
    Mixin — add to any Pydantic model that receives LLM output.
    Converts string "null" / "none" / "" to proper None / [] / 0
    before Pydantic type validation runs.
    """

    @field_validator('*', mode='before')
    @classmethod
    def clean_null_strings(cls, v):
        if isinstance(v, str) and v.strip().lower() in NULL_STRINGS:
            return None
        return v