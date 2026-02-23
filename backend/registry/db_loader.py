from sqlalchemy import func
from backend.db_models import Document

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
        raise ValueError(f"Document not found in DB: {department}/{document_filename}")

    # Ensure sections is a list
    sections = doc.sections
    if not isinstance(sections, list):
        sections = []
    
    # Ensure input_groups is a list (document-specific groups)
    input_groups = doc.input_groups
    if not isinstance(input_groups, list):
        input_groups = []

    return {
        "document_name": doc.document_name,
        "internal_type": doc.internal_type,
        "risk_level": doc.risk_level,
        "approval_required": doc.approval_required,
        "versioning_strategy": doc.versioning_strategy,
        "sections": sections,
        "input_groups": input_groups,
        "department": doc.department
    }
