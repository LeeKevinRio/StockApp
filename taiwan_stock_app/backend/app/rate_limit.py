"""
Rate Limiting 設定 — 使用 slowapi
"""
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request
from fastapi.responses import JSONResponse


def _key_func(request: Request) -> str:
    """從 request 取得 client IP 作為 rate limit key"""
    return get_remote_address(request)


# 全域 limiter 實例
limiter = Limiter(key_func=_key_func, default_limits=["60/minute"])


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Rate limit 超過時的回應"""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "請求過於頻繁，請稍後再試。(Rate limit exceeded, please try again later.)",
        },
    )
