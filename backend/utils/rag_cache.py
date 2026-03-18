import json
import hashlib
from backend.utils.redis_client import redis_client
from backend.utils.logger import get_logger
logger = get_logger("CACHE")

def generate_rag_cache_key(query: str, filters: dict):
    key_data = {
        "query": query.lower().strip(),
        "filters": filters or {}
    }

    key_str = json.dumps(key_data, sort_keys=True)
    return "rag:" + hashlib.md5(key_str.encode()).hexdigest()


def get_rag_cache(key: str):
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
    try:
        redis_client.set(key, json.dumps(value), ex=ttl)
        logger.info(f"Cache SET: {key}")
    except Exception as e:
        logger.error(f"Cache write error: {e}")