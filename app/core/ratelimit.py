from fastapi import Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from app.connectors.redis_connector import get_redis

# Limiter: 100 requests/min per IP
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

BLOCK_DURATION = 3600  # 1 hour


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    ip = request.client.host
    try:
        redis = await get_redis()
        if redis:
            await redis.set(f"blocked_ip:{ip}", 1, ex=BLOCK_DURATION)
    except Exception as e:
        print(f"⚠️ Redis not available for IP blocking: {e}")

    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "message": f"Too many requests. Your IP is blocked for {BLOCK_DURATION // 60} minutes."
        },
    )


# ASGI-compatible IP Block Middleware
class BlockIPMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        ip = scope["client"][0]
        is_blocked = None
        try:
            redis = await get_redis()
            if redis:
                is_blocked = await redis.get(f"blocked_ip:{ip}")
        except Exception as e:
            print(f"⚠️ Redis unavailable in IP block check: {e}")

        if is_blocked:
            response = JSONResponse(
                {"message": "Your IP is temporarily blocked."},
                status_code=status.HTTP_403_FORBIDDEN,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
