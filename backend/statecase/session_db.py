from backend.database import SessionLocal
from backend.db_models import AssistantSession


def get_session_db(session_id: str):
    """
    Fetch session data from the database.

    Args:
        session_id (str): Unique identifier for the session

    Returns:
        dict: Session data containing:
            - history (list): Stored conversation messages
            - context (dict): Stored metadata (filters, doc info, etc.)

    Notes:
        - Returns empty structure if session does not exist.
        - Ensures DB connection is safely closed after operation.
    """
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
    """
    Save or update session data in the database.

    Args:
        session_id (str): Unique session identifier
        history (list): Conversation history to persist
        context (dict): Session metadata to persist

    Returns:
        None

    Behavior:
        - Updates existing session if found
        - Creates new session if not found
        - Commits transaction to database

    Notes:
        - Uses session_id as user_id (can be extended later)
    """
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