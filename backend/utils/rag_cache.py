"""
RAG Redis Cache Utility

This module provides caching support for RAG queries.

Responsibilities:
- Generate unique cache keys based on query + filters
- Store RAG responses in Redis
- Retrieve cached responses to avoid recomputation

Key Features:
- Hash-based cache keys for consistency
- TTL-based expiration
- Improves response time and reduces LLM calls

Used by:
- query_search_engine
"""

import json
import hashlib
from backend.utils.redis_client import redis_client
from backend.utils.logger import get_logger
logger = get_logger("CACHE")

def generate_rag_cache_key(query: str, filters: dict):
    """
    Generate a unique cache key for a RAG query.

    Combines:
    - Normalized query
    - Metadata filters

    Uses MD5 hashing to create compact key.

    Args:
        query (str): Refined query
        filters (dict): Metadata filters

    Returns:
        str: Redis cache key
    """
    key_data = {
        "query": query.lower().strip(),
        "filters": filters or {}
    }

    key_str = json.dumps(key_data, sort_keys=True)
    return "rag:" + hashlib.md5(key_str.encode()).hexdigest()


def get_rag_cache(key: str):
    """
    Retrieve cached RAG response from Redis.

    Args:
        key (str): Cache key

    Returns:
        dict or None: Cached response if exists, else None

    Notes:
    - Handles JSON deserialization
    - Logs cache hits for debugging
    """
    try:
        data = redis_client.get(key)
        if data:
            logger.info(f"Cache HIT: {key}")
            return json.loads(data)
        else:
            logger.info(f"Cache MISS: {key}")
    except Exception as e:
        logger.error(f"Cache read error: {e}")
    return None


def set_rag_cache(key: str, value: dict, ttl=3600):
    """
    Store RAG response in Redis cache.

    Args:
        key (str): Cache key
        value (dict): Response payload
        ttl (int): Time-to-live in seconds

    Notes:
    - Serializes data to JSON
    - Improves performance for repeated queries
    """
    try:
        redis_client.set(key, json.dumps(value), ex=ttl)
        logger.info(f"Cache SET: {key}")
    except Exception as e:
        logger.error(f"Cache write error: {e}")