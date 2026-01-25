from pydantic import BaseModel
from typing import Any
from app.services.normalization.text import TextNormalizer

PRESERVE_FIELDS = {
    "operator",
    "resume_id",
    "job_id",
    "email",
    "linkedin",
    "phone",
}

def normalize_object(obj: Any):
    if isinstance(obj, list):
        return [normalize_object(i) for i in obj]

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

    if isinstance(obj, str):
        return TextNormalizer.normalize(obj)

    return obj
