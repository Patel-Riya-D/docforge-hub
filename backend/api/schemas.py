from pydantic import BaseModel
from typing import List, Optional
from typing import List, Dict, Any

class DocumentPreviewRequest(BaseModel):
    department: str
    document_filename: str


class Section(BaseModel):
    name: str
    mandatory: bool


class DocumentPreviewResponse(BaseModel):
    document_name: str
    department: str
    internal_type: str
    risk_level: str
    approval_required: bool
    versioning_strategy: str | None
    sections: List[Section]
    allowed_formats: List[str]
    input_groups: Optional[List[Dict[str, Any]]]

class DocumentGenerateRequest(BaseModel):
    department: str
    document_filename: str
    user_notes: Optional[str] = None
    company_profile: Optional[Dict[str, Any]] = None
    document_inputs: Optional[Dict[str, Any]] = None

class DocumentGenerateResponse(BaseModel):
    draft_id: str
    document_name: str
    department: str
    internal_type: str
    version: str
    status: str
    sections: List[Dict[str, Any]]
    approval_required: bool
