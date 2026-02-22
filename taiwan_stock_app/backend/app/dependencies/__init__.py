"""
Dependencies — FastAPI 依賴注入
"""
from .ai_quota import check_ai_quota, AIQuotaContext

__all__ = ["check_ai_quota", "AIQuotaContext"]
