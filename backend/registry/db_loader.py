from sqlalchemy import func
from backend.models import Document

def load_document_from_db(
    db,
    department: str,
    document_filename: str
):
    doc = db.query(Document).filter(
        func.lower(Document.department) == department.lower(),
        func.lower(Document.document_name) == document_filename.lower()
    ).first()

    if not doc:
        raise ValueError("Document not found in DB")

    return {
        "document_name": doc.document_name,
        "internal_type": doc.internal_type,
        "risk_level": doc.risk_level,
        "approval_required": doc.approval_required,
        "versioning_strategy": doc.versioning_strategy,
        "sections": doc.sections,
        "input_groups": doc.input_groups
    }
