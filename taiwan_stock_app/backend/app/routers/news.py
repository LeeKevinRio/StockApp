"""
新聞路由 - 支援台股與美股
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models import User
from app.schemas.news import NewsResponse, NewsListResponse, MarketNewsResponse
from app.services.news_service import news_service
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/stock/{stock_id}")
async def get_stock_news(
    stock_id: str,
    market: str = Query("TW", description="Market: TW or US"),
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得個股新聞

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW" (台股) 或 "US" (美股)
        limit: 返回數量限制 (預設 10)

    Returns:
        個股新聞列表
    """
    try:
        news_list = await news_service.get_stock_news(db, stock_id, limit, market=market)
        return {
            "stock_id": stock_id,
            "market": market,
            "total": len(news_list),
            "news": news_list,
            "source": "Taiwan News" if market == "TW" else "Global News",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取新聞失敗: {str(e)}")


@router.get("/market")
async def get_market_news(
    market: str = Query("TW", description="Market: TW or US"),
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得市場新聞

    Args:
        market: 市場 - "TW" (台股) 或 "US" (美股)
        limit: 返回數量限制 (預設 20)

    Returns:
        市場新聞列表
    """
    try:
        news_list = await news_service.get_market_news(db, limit, market=market)
        return {
            "market": market,
            "total": len(news_list),
            "news": news_list,
            "source": "Taiwan News" if market == "TW" else "Global News",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取市場新聞失敗: {str(e)}")
