from backend.database import SessionLocal
from backend.db_models import AssistantSession


def get_session_db(session_id: str):
    db = SessionLocal()
    try:
        session = db.query(AssistantSession).filter_by(session_id=session_id).first()

        if not session:
            return {"history": [], "context": {}}

        return {
            "history": session.history or [],
            "context": session.context or {}
        }
    finally:
        db.close()


def save_session_db(session_id: str, history, context):
    db = SessionLocal()
    try:
        session = db.query(AssistantSession).filter_by(session_id=session_id).first()

        if session:
            session.history = history
            session.context = context
        else:
            session = AssistantSession(
                session_id=session_id,
                history=history,
                context=context,
                user_id=session_id
            )
            db.add(session)

        db.commit()
    finally:
        db.close()