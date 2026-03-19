"""
rate_limitter.py

This module implements a simple rate limiting mechanism using Redis
for the DocForge Hub system.

It restricts the number of requests a user can make within a fixed time window.

Key Features:
- Per-user request tracking using Redis
- Configurable request limit and time window
- Lightweight and fast (in-memory Redis operations)

Default Behavior:
- Maximum 10 requests per 60 seconds per user

This module is used to:
- Prevent API abuse
- Protect LLM endpoints from excessive usage
- Ensure fair usage across users
"""
from backend.utils.redis_client import redis_client
import time

RATE_LIMIT = 10   # max requests
WINDOW = 60       # seconds

def check_rate_limit(user_id: str):
    """
    Check whether a user has exceeded the allowed request rate.

    This function uses Redis to track the number of requests
    made by a user within a defined time window.

    Args:
        user_id (str): Unique identifier for the user/session.

    Returns:
        bool:
            - True → Request allowed
            - False → Rate limit exceeded

    Workflow:
        1. Generate Redis key for user (rate:{user_id})
        2. Check current request count
        3. If count exceeds limit → block request
        4. Otherwise increment counter
        5. Set expiration for new keys (WINDOW)

    Configuration:
        RATE_LIMIT (int): Max requests allowed (default: 10)
        WINDOW (int): Time window in seconds (default: 60)

    Example:
        if not check_rate_limit(user_id):
            raise HTTPException(status_code=429, detail="Too many requests")

    Notes:
        - Uses Redis for fast, scalable rate limiting
        - Counter resets automatically after expiration
        - Suitable for protecting high-cost endpoints (e.g., LLM calls)
    """
    key = f"rate:{user_id}"

    current = redis_client.get(key)

    if current:
        if int(current) >= RATE_LIMIT:
            return False
        else:
            redis_client.incr(key)
    else:
        redis_client.set(key, 1, ex=WINDOW)

    return True