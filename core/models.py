from pydantic import BaseModel, Field
from typing import List

class FileObject(BaseModel):
    id: int
    name: str
    ext: str
    size: int
    original_path: str  # Kept internal, not sent to LLM

class Group(BaseModel):
    folder_name: str = Field(description="Highly specific name for the folder (e.g. '2023 Tax Invoices' not 'Documents')")
    reason: str = Field(description="Short reason why these files were grouped together")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0")
    file_ids: List[int] = Field(description="List of integer file IDs that belong in this group")

class OrganizationPlan(BaseModel):
    summary: str = Field(description="One sentence summary of what was organized")
    groups: List[Group] = Field(description="List of logical groupings")
