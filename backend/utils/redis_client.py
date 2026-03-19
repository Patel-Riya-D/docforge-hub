"""
redis_client.py

This module initializes and exposes a Redis client instance
for the DocForge Hub system.

It provides a centralized connection to Redis, enabling:
- Rate limiting (API protection)
- Session storage
- Caching (future use)

Configuration:
- Host: localhost
- Port: 6379
- decode_responses=True → returns strings instead of bytes

This module ensures a single reusable Redis connection
across the entire application.
"""
import redis

"""
Redis client instance for interacting with the Redis server.

This client is used across the application for:
- Rate limiting (tracking request counts)
- Session management
- Temporary data storage

Attributes:
    host (str): Redis server host (default: localhost)
    port (int): Redis server port (default: 6379)
    decode_responses (bool): Ensures responses are returned as strings

Notes:
    - Ensure Redis server is running before using this client
    - In production, configuration should be moved to environment variables
"""

redis_client = redis.Redis(
    host="localhost",
    port=6379,
    decode_responses=True
)