from sqlalchemy import func
from backend.db_models import Document
from backend.utils.redis_client import redis_client
import json
from backend.utils.logger import get_logger
import time

logger = get_logger("DB_LOADER")


def load_document_from_db(
    db,
    department: str,
    document_filename: str
):

    start_time = time.time()

    logger.info(f"Loading document: {department}/{document_filename}")

    cache_key = f"doc:{department.lower()}:{document_filename.lower()}"

    # -------------------------
    # ⚡ Try Redis First
    # -------------------------
    try:
        cached_doc = redis_client.get(cache_key)

        if cached_doc:
            logger.info(f"Cache HIT: {cache_key}")
            try:
                return json.loads(cached_doc)
            except Exception:
                logger.warning("Cache corrupted, loading from DB")

        else:
            logger.info(f"Cache MISS: {cache_key}")

    except Exception as e:
        logger.error(f"Redis read failed: {str(e)}")

    # -------------------------
    # 🗄️ Query Database
    # -------------------------
    logger.info("Querying database...")

    try:
        doc = db.query(Document).filter(
            func.lower(Document.department) == department.lower(),
            func.lower(Document.document_name) == document_filename.lower()
        ).first()
    except Exception as e:
        logger.error(f"DB query failed: {str(e)}")
        raise

    if not doc:
        logger.warning(f"Document not found: {department}/{document_filename}")
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
    # 💾 Save to Redis
    # -------------------------
    try:
        redis_client.set(cache_key, json.dumps(result, default=str), ex=3600)
        logger.info(f"Cache SET: {cache_key}")
    except Exception as e:
        logger.error(f"Redis write failed: {str(e)}")

    end_time = time.time()
    logger.info(f"DB loader response time: {round(end_time - start_time, 2)} sec")

    return result