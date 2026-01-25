from typing import Optional,List
from pydantic import BaseModel
class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None