"""
redis_session.py

This module manages user session data using Redis for the DocForge Hub system.

It enables lightweight, fast, and temporary session storage for:
- Tracking user interaction history (e.g., RAG queries)
- Maintaining conversational context
- Supporting stateful user experiences

Key Features:
- Session storage with expiration (TTL)
- JSON-based data persistence
- Limited history retention for efficiency

Default Configuration:
- Session TTL: 1 hour
- History size: last 5 user queries

This module is essential for enabling context-aware features
like conversational RAG and personalized responses.
"""
import json
from backend.utils.redis_client import redis_client

SESSION_TTL = 3600  # 1 hour

def save_user_session(session_id: str, data: dict):
    """
    Save user session data in Redis.

    Args:
        session_id (str): Unique session identifier.
        data (dict): Session data to store.

    Returns:
        None

    Behavior:
        - Serializes data to JSON
        - Stores it in Redis with expiration (TTL)
        - Overwrites existing session data

    Notes:
        - TTL ensures automatic cleanup after inactivity
        - Used for maintaining temporary user state
    """
    key = f"session:{session_id}"
    redis_client.set(key, json.dumps(data), ex=SESSION_TTL)

def get_user_session(session_id: str):
    """
    Retrieve user session data from Redis.

    Args:
        session_id (str): Unique session identifier.

    Returns:
        dict: Session data if found, otherwise empty dict.

    Behavior:
        - Fetches JSON string from Redis
        - Deserializes into Python dictionary
        - Returns empty dict if session does not exist

    Notes:
        - Used for retrieving conversation history or user context
    """
    key = f"session:{session_id}"
    data = redis_client.get(key)
    return json.loads(data) if data else {}

def update_session_history(session_id: str, question: str):
    """
    Update user session with latest query history.

    This function:
    - Retrieves existing session data
    - Appends new user question
    - Keeps only the last 5 queries
    - Saves updated session back to Redis

    Args:
        session_id (str): Unique session identifier.
        question (str): User query to store.

    Returns:
        None

    Behavior:
        - Maintains rolling history (max 5 entries)
        - Prevents session data from growing indefinitely

    Notes:
        - Used in RAG pipeline for context-aware responses
        - Improves conversational continuity
    """
    session = get_user_session(session_id)

    history = session.get("history", [])
    history.append(question)

    session["history"] = history[-5:]  # keep last 5 queries

    save_user_session(session_id, session)