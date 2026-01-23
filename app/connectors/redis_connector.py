import os
import redis.asyncio as redis

REDIS_URL = os.getenv("REDIS_URL", "redis://10.140.243.37:6379")

_redis = None


async def get_redis():
    global _redis
    if _redis is None:
        try:
            _redis = redis.from_url(REDIS_URL, decode_responses=True)
            # Test connection
            await _redis.ping()
            print("✅ Connected to Redis")
        except Exception as e:
            print(f"⚠️ Redis connection failed: {e}")
            _redis = None
    return _redis
