"""
AI Stock Discovery Router - AI 潛力股掃描 API
"""
import logging
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.services.ai_discovery_service import AIDiscoveryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai/discovery", tags=["ai-discovery"])

# 簡易快取：每日每市場只掃描一次
_cache: dict = {}
_cache_date: Optional[date] = None


def _get_cached(market: str) -> Optional[dict]:
    global _cache_date
    today = date.today()
    if _cache_date != today:
        _cache.clear()
        _cache_date = today
    return _cache.get(market)


def _set_cache(market: str, data: dict):
    global _cache_date
    _cache_date = date.today()
    _cache[market] = data


@router.get("")
def discover_stocks(
    market: str = Query("TW", description="市場: TW 或 US"),
    refresh: bool = Query(False, description="強制重新掃描"),
    top_n: int = Query(5, ge=1, le=10, description="推薦股票數量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    AI 潛力股掃描：自動分析市場，找出短期（5天）高機率上漲的股票

    不需要自選股 — 系統主動掃描全市場候選股票池
    """
    # 檢查快取
    if not refresh:
        cached = _get_cached(market)
        if cached:
            logger.info(f"[Discovery] Returning cached {market} picks")
            return cached

    # 執行掃描
    logger.info(f"[Discovery] Starting {market} scan for user {current_user.id}")
    service = AIDiscoveryService(
        subscription_tier=getattr(current_user, "subscription_tier", "free") or "free"
    )
    result = service.discover_stocks(market=market, top_n=top_n)

    # 快取結果
    _set_cache(market, result)

    return result


@router.get("/quick")
def quick_discover(
    market: str = Query("TW", description="市場: TW 或 US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    快速版本：只返回快取的結果，不觸發新掃描
    適合首頁 Dashboard 快速載入
    """
    cached = _get_cached(market)
    if cached:
        return cached

    # 無快取時返回空結果
    return {
        "market": market,
        "scan_date": date.today().isoformat(),
        "analysis_period": "5 trading days",
        "picks": [],
        "market_summary": "尚未掃描，請點擊刷新觸發 AI 分析",
        "cached": False,
    }
