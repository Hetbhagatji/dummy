from pydantic import BaseModel, Field
from typing import Optional

class Location(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class ContactInformation(BaseModel):
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    location: Optional[Location] = Field(
        None,
        description="City, State, Country format"
    )


class PersonalInfo(BaseModel):
    full_name: Optional[str] = None
    contact: Optional[ContactInformation] = None
    professional_summary: Optional[str] = Field(
        None,
        description="Professional summary for any industry"
    )
