from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from enum import Enum
import uuid


class ApprovalStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentApproval(BaseModel):
    request_id: str
    department: str
    document_filename: str
    status: ApprovalStatus
    requested_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
