"""
市場概覽 API
GET /api/market/heatmap - 產業熱力圖
GET /api/market/rankings - 漲跌排行
"""
from fastapi import APIRouter, Query

from app.services.market_overview_service import MarketOverviewService

router = APIRouter(prefix="/api/market", tags=["Market Overview"])

_service = MarketOverviewService()


@router.get("/heatmap")
def get_heatmap(market: str = Query("TW", description="市場: TW 或 US")):
    """取得產業熱力圖數據"""
    return _service.get_heatmap_data(market=market)


@router.get("/rankings")
def get_rankings(
    market: str = Query("TW", description="市場: TW 或 US"),
    category: str = Query("gainers", description="排行類別: gainers, losers, volume, active"),
    limit: int = Query(20, ge=1, le=50, description="回傳筆數"),
):
    """取得漲跌排行"""
    return _service.get_rankings(market=market, category=category, limit=limit)
