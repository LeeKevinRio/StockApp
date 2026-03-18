"""
社群情緒分析路由 - 支援台股(PTT/Dcard/Mobile01/Threads)與美股(Reddit/Threads)
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models import User, Stock
from app.schemas.social import HotStockResponse, SocialAnalysisResponse
from app.services.sentiment_service import sentiment_service
from app.data_fetchers.reddit_fetcher import reddit_fetcher
from app.data_fetchers.threads_fetcher import threads_fetcher
from app.data_fetchers.taiwan_social_fetcher import taiwan_social_fetcher
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/social", tags=["social"])


def _merge_hot_stocks(primary: List[dict], secondary: List[dict]) -> List[dict]:
    """合併兩個來源的熱門股票，相同股票合併計數"""
    merged = {s["stock_id"]: dict(s) for s in primary}

    for s in secondary:
        sid = s["stock_id"]
        if sid in merged:
            # 合併：加總 mention_count，平均 sentiment
            merged[sid]["mention_count"] += s.get("mention_count", 0)
            old_score = merged[sid].get("sentiment_score", 0)
            new_score = s.get("sentiment_score", 0)
            merged[sid]["sentiment_score"] = round((old_score + new_score) / 2, 2)
            # 合併 sample_posts
            existing_posts = merged[sid].get("sample_posts", [])
            new_posts = s.get("sample_posts", [])
            merged[sid]["sample_posts"] = (existing_posts + new_posts)[:5]
        else:
            merged[sid] = dict(s)

    result = list(merged.values())
    result.sort(key=lambda x: x.get("mention_count", 0), reverse=True)
    return result


def _merge_market_sentiment(primary: dict, secondary: dict) -> dict:
    """合併兩個來源的市場情緒"""
    total_p = primary.get("total", 0)
    total_s = secondary.get("total", 0)
    total = total_p + total_s

    if total == 0:
        return primary

    merged = {
        "total": total,
        "positive": primary.get("positive", 0) + secondary.get("positive", 0),
        "negative": primary.get("negative", 0) + secondary.get("negative", 0),
        "neutral": primary.get("neutral", 0) + secondary.get("neutral", 0),
    }

    # 加權平均情緒分數（以貼文數量為權重）
    score_p = primary.get("score", 0) * total_p
    score_s = secondary.get("score", 0) * total_s
    merged["score"] = round((score_p + score_s) / total, 2) if total > 0 else 0

    if merged["score"] > 0.1:
        merged["overall"] = "positive"
    elif merged["score"] < -0.1:
        merged["overall"] = "negative"
    else:
        merged["overall"] = "neutral"

    return merged


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
            # Reddit + Threads for US stocks
            hot_stocks = reddit_fetcher.get_hot_stocks(limit)

            # 嘗試合併 Threads 數據
            try:
                threads_stocks = threads_fetcher.get_hot_stocks(market="US", limit=limit)
                hot_stocks = _merge_hot_stocks(hot_stocks, threads_stocks)
            except Exception as e:
                logger.warning(f"Threads US hot stocks fallback: {e}")

            hot_stocks = hot_stocks[:limit]
            return {
                'total': len(hot_stocks),
                'stocks': hot_stocks,
                'source': 'Reddit + Threads',
                'sources': ['r/wallstreetbets', 'r/stocks', 'r/investing', 'r/options', 'r/StockMarket', 'Threads'],
                'market': 'US',
            }
        else:
            # PTT/Dcard/Mobile01 + Threads for Taiwan stocks
            hot_stocks = taiwan_social_fetcher.get_hot_stocks(limit)

            # 嘗試合併 Threads 數據
            try:
                threads_stocks = threads_fetcher.get_hot_stocks(market="TW", limit=limit)
                hot_stocks = _merge_hot_stocks(hot_stocks, threads_stocks)
            except Exception as e:
                logger.warning(f"Threads TW hot stocks fallback: {e}")

            # Enrich with stock names from database
            for stock in hot_stocks:
                if not stock.get("stock_name"):
                    stock["stock_name"] = get_stock_name(db, stock["stock_id"])

            hot_stocks = hot_stocks[:limit]
            return {
                'total': len(hot_stocks),
                'stocks': hot_stocks,
                'source': 'Taiwan Social + Threads',
                'sources': ['PTT', 'Dcard', 'Mobile01', 'Threads'],
                'market': 'TW',
            }
    except Exception as e:
        logger.error(f"Hot stocks error: {e}")
        raise HTTPException(status_code=500, detail="獲取熱門股票失敗，請稍後再試")


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
            # Reddit + Threads for US stocks
            posts = reddit_fetcher.fetch_stock_discussions(stock_id, limit=30)

            # 合併 Threads 討論
            try:
                threads_posts = threads_fetcher.fetch_stock_discussions(stock_id, market="US", limit=10)
                for tp in threads_posts:
                    posts.append({
                        "id": tp.get("id"),
                        "title": tp.get("title", ""),
                        "content": tp.get("content", ""),
                        "author": tp.get("author", ""),
                        "subreddit": "Threads",
                        "url": tp.get("url", ""),
                        "score": tp.get("like_count", 0),
                        "num_comments": tp.get("reply_count", 0),
                        "sentiment": tp.get("sentiment", "neutral"),
                        "sentiment_score": tp.get("sentiment_score", 0),
                        "posted_at": tp.get("posted_at"),
                        "platform": "threads",
                    })
            except Exception as e:
                logger.warning(f"Threads stock discussions fallback: {e}")

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
                platform = p.get("platform", "reddit")
                board = "Threads" if platform == "threads" else f"r/{p.get('subreddit', 'stocks')}"
                formatted_posts.append({
                    "id": p.get("id"),
                    "platform": platform,
                    "board": board,
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
                "source": "Reddit + Threads",
                "sources": ['r/wallstreetbets', 'r/stocks', 'r/investing', 'Threads'],
                "market": "US",
            }
        else:
            # Taiwan: existing sentiment service + Threads
            result = await sentiment_service.get_stock_sentiment(db, stock_id, days)
            result["source"] = "Taiwan Social + Threads"
            result["sources"] = ["PTT", "Dcard", "Mobile01", "Threads"]

            # 合併 Threads 討論
            try:
                threads_posts = threads_fetcher.fetch_stock_discussions(stock_id, market="TW", limit=10)
                if threads_posts:
                    existing_posts = result.get("recent_posts", [])
                    for tp in threads_posts:
                        existing_posts.append({
                            "id": tp.get("id"),
                            "platform": "threads",
                            "board": "Threads",
                            "title": tp.get("title", ""),
                            "content": tp.get("content", ""),
                            "author": tp.get("author", ""),
                            "url": tp.get("url", ""),
                            "sentiment": tp.get("sentiment", "neutral"),
                            "sentiment_score": tp.get("sentiment_score", 0),
                            "push_count": tp.get("like_count", 0),
                            "boo_count": 0,
                            "comment_count": tp.get("reply_count", 0),
                            "posted_at": tp.get("posted_at"),
                        })
                    result["recent_posts"] = existing_posts[:15]
                    result["total_mentions"] = result.get("total_mentions", 0) + len(threads_posts)
            except Exception as e:
                logger.warning(f"Threads TW stock discussions fallback: {e}")

            result["market"] = "TW"
            return result
    except Exception as e:
        logger.error(f"Stock sentiment error: {e}")
        raise HTTPException(status_code=500, detail="獲取情緒分析失敗，請稍後再試")


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
            # Reddit + Threads for US market sentiment
            result = reddit_fetcher.get_market_sentiment()

            # 合併 Threads 市場情緒
            try:
                threads_sentiment = threads_fetcher.get_market_sentiment(market="US")
                result = _merge_market_sentiment(result, threads_sentiment)
            except Exception as e:
                logger.warning(f"Threads US market sentiment fallback: {e}")

            result["source"] = "Reddit + Threads"
            result["sources"] = ['r/wallstreetbets', 'r/stocks', 'r/investing', 'r/options', 'r/StockMarket', 'Threads']
            result["market"] = "US"
            return result
        else:
            # Taiwan social + Threads for market sentiment
            result = taiwan_social_fetcher.get_market_sentiment()

            # 合併 Threads 市場情緒
            try:
                threads_sentiment = threads_fetcher.get_market_sentiment(market="TW")
                result = _merge_market_sentiment(result, threads_sentiment)
            except Exception as e:
                logger.warning(f"Threads TW market sentiment fallback: {e}")

            result["source"] = "Taiwan Social + Threads"
            result["sources"] = ["PTT", "Dcard", "Mobile01", "Threads"]
            result["market"] = "TW"
            return result
    except Exception as e:
        logger.error(f"Market sentiment error: {e}")
        raise HTTPException(status_code=500, detail="獲取市場情緒失敗，請稍後再試")
