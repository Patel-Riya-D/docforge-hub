from sqlalchemy import func
from backend.db_models import Document
from backend.utils.redis_client import redis_client
import json


def load_document_from_db(
    db,
    department: str,
    document_filename: str
):

    cache_key = f"doc:{department.lower()}:{document_filename.lower()}"

    # -------------------------
    # Try Redis First
    # -------------------------
    try:
        cached_doc = redis_client.get(cache_key)

        if cached_doc:
            try:
                print("REDIS CACHE HIT:", cache_key)
                return json.loads(cached_doc)
            except Exception:
                print("REDIS CACHE MISS:", cache_key)
                print("Redis cache corrupted, loading from DB")

    except Exception as e:
        print("Redis cache read failed:", e)

    # -------------------------
    # Query Database
    # -------------------------
    doc = db.query(Document).filter(
        func.lower(Document.department) == department.lower(),
        func.lower(Document.document_name) == document_filename.lower()
    ).first()

    if not doc:
        raise ValueError(f"Document not found in DB: {department}/{document_filename}")

    sections = doc.sections if isinstance(doc.sections, list) else []
    input_groups = doc.input_groups if isinstance(doc.input_groups, list) else []

    result = {
        "document_name": doc.document_name,
        "internal_type": doc.internal_type,
        "risk_level": doc.risk_level,
        "approval_required": doc.approval_required,
        "versioning_strategy": doc.versioning_strategy,
        "sections": sections,
        "input_groups": input_groups,
        "department": doc.department
    }

    # -------------------------
    # Save to Redis
    # -------------------------
    try:
        redis_client.set(cache_key, json.dumps(result, default=str), ex=3600)
    except Exception as e:
        print("Redis cache write failed:", e)

    return result