import json
import os
from datetime import datetime, timezone
from typing import List
from .models import DocumentApproval, ApprovalStatus
import uuid

DATA_FILE = "backend/data/approvals.json"


def _load():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def _save(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, default=str)


def create_request(department, document_filename):
    data = _load()

    record = {
        "request_id": str(uuid.uuid4()),
        "department": department,
        "document_filename": document_filename,
        "status": ApprovalStatus.PENDING_APPROVAL,
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "approved_at": None,
        "approved_by": None
    }

    data.append(record)
    _save(data)
    return record


def list_pending():
    return [
        r for r in _load()
        if r["status"] == ApprovalStatus.PENDING_APPROVAL
    ]


def approve(request_id, admin="admin"):
    data = _load()

    for r in data:
        if r["request_id"] == request_id:
            r["status"] = ApprovalStatus.APPROVED
            r["approved_at"] = datetime.utcnow().isoformat()
            r["approved_by"] = admin
            _save(data)
            return r

    raise ValueError("Request not found")
