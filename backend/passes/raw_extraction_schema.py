from pydantic import BaseModel
from typing import List, Optional


class RawItem(BaseModel):
    text: str                  # exact surface form
    type: str                  # skill | experience | degree | certification | responsibility | salary | metadata
    sentence_id: int           # where it appeared
    span_hint: Optional[str] = None   # optional nearby phrase


class RawSentence(BaseModel):
    sentence_id: int
    raw_text: str
    items: List[RawItem]


class RawJobExtraction(BaseModel):
    sentences: List[RawSentence]
