from pydantic import BaseModel
from typing import Any
from app.services.normalization_service import TextNormalizer

PRESERVE_FIELDS = {
    "operator",
    "resume_id",
    "job_id",
    "email",
    "linkedin",
    "phone",
}

def normalize_object(obj: Any):
    # LIST
    if isinstance(obj, list):
        return [normalize_object(i) for i in obj]

    # DICT (🔥 MISSING PART)
    if isinstance(obj, dict):
        return {
            key: normalize_object(value)
            if key not in PRESERVE_FIELDS
            else value
            for key, value in obj.items()
        }

    # PYDANTIC MODEL
    if isinstance(obj, BaseModel):
        data = {}
        for field, value in obj.model_dump().items():
            if value is None:
                data[field] = None
            elif field in PRESERVE_FIELDS:
                data[field] = value
            else:
                data[field] = normalize_object(value)

        return obj.__class__(**data)

    # STRING
    if isinstance(obj, str):
        return TextNormalizer.normalize(obj)

    return obj
