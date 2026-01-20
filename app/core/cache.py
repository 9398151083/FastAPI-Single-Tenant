# app/core/cache.py
import asyncio
from app.connectors.redis_connector import get_redis
import logging

logger = logging.getLogger("cache")
CACHE_TTL = 300  # seconds, default TTL for cached items


async def set_cache(key: str, value: dict, ttl: int = CACHE_TTL):
    try:
        redis = await get_redis()
        if redis:
            await redis.set(key, value, ex=ttl)
    except Exception as e:
        logger.warning(f"Redis SET failed for key {key}: {e}")


async def get_cache(key: str):
    try:
        redis = await get_redis()
        if redis:
            value = await redis.get(key)
            return value
    except Exception as e:
        logger.warning(f"Redis GET failed for key {key}: {e}")
    return None


async def invalidate_cache(pattern: str):
    """Delete keys matching a pattern."""
    try:
        redis = await get_redis()
        if not redis:
            return
        # Scan & delete keys matching pattern
        cursor = b"0"
        while cursor:
            cursor, keys = await redis.scan(cursor=cursor, match=pattern, count=100)
            if keys:
                await redis.delete(*keys)
            if cursor == b"0":
                break
    except Exception as e:
        logger.warning(f"Redis invalidation failed for pattern {pattern}: {e}")
