"""
社群情緒分析路由 - 支援台股(PTT/Dcard/Mobile01)與美股(Reddit)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Stock
from app.schemas.social import HotStockResponse, SocialAnalysisResponse
from app.services.sentiment_service import sentiment_service
from app.data_fetchers.reddit_fetcher import reddit_fetcher
from app.data_fetchers.taiwan_social_fetcher import taiwan_social_fetcher
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/social", tags=["social"])


def get_stock_name(db: Session, stock_id: str) -> str:
    """Get stock name from database"""
    stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
    return stock.name if stock else None


@router.get("/hot-stocks")
async def get_hot_stocks(
    market: str = Query("TW", description="Market: TW (PTT/Dcard/Mobile01) or US (Reddit)"),
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得熱門討論股票

    Args:
        market: 市場 - "TW"(PTT/Dcard/Mobile01) 或 "US"(Reddit)
        limit: 返回數量限制 (預設 10)

    Returns:
        熱門股票列表
    """
    try:
        if market == "US":
            # Use Reddit for US stocks
            hot_stocks = reddit_fetcher.get_hot_stocks(limit)
            return {
                'total': len(hot_stocks),
                'stocks': hot_stocks,
                'source': 'Reddit',
                'sources': ['r/wallstreetbets', 'r/stocks', 'r/investing', 'r/options', 'r/StockMarket'],
                'market': 'US',
            }
        else:
            # Use multiple Taiwan social platforms
            hot_stocks = taiwan_social_fetcher.get_hot_stocks(limit)

            # Enrich with stock names from database
            for stock in hot_stocks:
                if not stock.get("stock_name"):
                    stock["stock_name"] = get_stock_name(db, stock["stock_id"])

            return {
                'total': len(hot_stocks),
                'stocks': hot_stocks,
                'source': 'Taiwan Social',
                'sources': ['PTT', 'Dcard', 'Mobile01'],
                'market': 'TW',
            }
    except Exception as e:
        print(f"Hot stocks error: {e}")
        raise HTTPException(status_code=500, detail=f"獲取熱門股票失敗: {str(e)}")


@router.get("/stock/{stock_id}/sentiment")
async def get_stock_sentiment(
    stock_id: str,
    market: str = Query("TW", description="Market: TW or US"),
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得個股社群情緒分析

    Args:
        stock_id: 股票代碼
        market: 市場 - "TW"(PTT/Dcard) 或 "US"(Reddit)
        days: 分析天數 (預設 7)

    Returns:
        社群情緒分析結果
    """
    try:
        if market == "US":
            # Use Reddit for US stocks
            posts = reddit_fetcher.fetch_stock_discussions(stock_id, limit=30)

            positive = sum(1 for p in posts if p.get("sentiment") == "positive")
            negative = sum(1 for p in posts if p.get("sentiment") == "negative")
            neutral = len(posts) - positive - negative
            total = len(posts)

            avg_score = sum(p.get("sentiment_score", 0) for p in posts) / total if total > 0 else 0

            if avg_score > 0.1:
                overall_sentiment = "positive"
            elif avg_score < -0.1:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"

            # Format posts for frontend
            formatted_posts = []
            for p in posts[:10]:
                formatted_posts.append({
                    "id": p.get("id"),
                    "platform": "reddit",
                    "board": f"r/{p.get('subreddit', 'stocks')}",
                    "title": p.get("title", ""),
                    "content": p.get("content", ""),
                    "author": p.get("author", ""),
                    "url": p.get("url", ""),
                    "sentiment": p.get("sentiment", "neutral"),
                    "sentiment_score": p.get("sentiment_score", 0),
                    "push_count": p.get("score", 0),
                    "boo_count": 0,
                    "comment_count": p.get("num_comments", 0),
                    "posted_at": p.get("posted_at"),
                })

            return {
                "stock_id": stock_id,
                "total_mentions": total,
                "sentiment_summary": {
                    "positive": positive,
                    "negative": negative,
                    "neutral": neutral,
                    "total": total,
                    "score": round(avg_score, 2),
                    "overall": overall_sentiment,
                },
                "overall_sentiment": overall_sentiment,
                "sentiment_score": round(avg_score, 2),
                "recent_posts": formatted_posts,
                "source": "Reddit",
                "sources": ['r/wallstreetbets', 'r/stocks', 'r/investing'],
                "market": "US",
            }
        else:
            # Use existing sentiment service for Taiwan stocks (includes PTT)
            result = await sentiment_service.get_stock_sentiment(db, stock_id, days)
            result["source"] = "Taiwan Social"
            result["sources"] = ["PTT", "Dcard", "Mobile01"]
            result["market"] = "TW"
            return result
    except Exception as e:
        print(f"Stock sentiment error: {e}")
        raise HTTPException(status_code=500, detail=f"獲取情緒分析失敗: {str(e)}")


@router.get("/market")
async def get_market_sentiment(
    market: str = Query("TW", description="Market: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得市場整體情緒

    Args:
        market: 市場 - "TW"(PTT/Dcard/Mobile01) 或 "US"(Reddit)

    Returns:
        市場情緒分析
    """
    try:
        if market == "US":
            # Use Reddit for US market sentiment
            result = reddit_fetcher.get_market_sentiment()
            result["source"] = "Reddit"
            result["sources"] = ['r/wallstreetbets', 'r/stocks', 'r/investing', 'r/options', 'r/StockMarket']
            result["market"] = "US"
            return result
        else:
            # Use Taiwan social fetcher for market sentiment
            result = taiwan_social_fetcher.get_market_sentiment()
            result["source"] = "Taiwan Social"
            result["market"] = "TW"
            return result
    except Exception as e:
        print(f"Market sentiment error: {e}")
        raise HTTPException(status_code=500, detail=f"獲取市場情緒失敗: {str(e)}")
