from pydantic import BaseModel, Field
from typing import Optional,List
class Certification(BaseModel):
    certification_name: Optional[str] = Field(
        None,
        description="""Universal certifications/licenses:
        - IT: AWS Certified, PMP, Scrum Master
        - Healthcare: Medical License (MD), RN License, BLS/ACLS
        - Pharma: GCP Certification, RAC
        - Finance: CFA, CPA, Series 7, FRM
        - Legal: Bar License (State specific)
        - General: Six Sigma, PRINCE2
        """
    )
    issuing_body: Optional[str] = Field(
        None,
        description="Issuing organization: AWS, PMI, State Medical Board, FINRA, State Bar, etc."
    )
   

class Certifications(BaseModel):
    entries: List[Certification] = Field(
        default_factory=list
    )
