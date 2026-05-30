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
    """
    取得 rate limit 的識別 key。

    部署在 Render／Railway 等雲端代理後面時，直接連線的來源 IP 會固定是代理 IP，
    導致所有使用者被視為同一人、限流形同虛設。
    因此優先採用代理帶上來的 X-Forwarded-For 最前面那個(原始 client IP)，
    取不到時才退回直接連線 IP。
    """
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # 格式可能是 "client, proxy1, proxy2"，取第一個非空 IP
        client_ip = forwarded.split(",")[0].strip()
        if client_ip:
            return client_ip
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
