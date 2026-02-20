"""
新聞服務 - 支援台股與美股
含 TTL 快取 + 情感摘要供 AI 整合使用
"""
import asyncio
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.news import StockNews
from app.data_fetchers.news_fetcher import news_fetcher
from app.data_fetchers.global_news_fetcher import global_news_fetcher

logger = logging.getLogger(__name__)

# 快取 TTL（30 分鐘）
NEWS_CACHE_TTL_MINUTES = 30


class NewsService:
    """新聞服務 - 支援台股與美股"""

    async def get_stock_news(
        self,
        db: Session,
        stock_id: str,
        limit: int = 10,
        use_cache: bool = True,
        market: str = "TW"
    ) -> List[dict]:
        """
        獲取個股新聞

        Args:
            db: 資料庫會話
            stock_id: 股票代碼
            limit: 返回數量限制
            use_cache: 是否使用快取
            market: 市場 - "TW" (台股) 或 "US" (美股)

        Returns:
            新聞列表
        """
        if market == "US":
            return await self._get_us_stock_news(stock_id, limit)
        else:
            return await self._get_tw_stock_news(db, stock_id, limit, use_cache)

    async def _get_tw_stock_news(
        self,
        db: Session,
        stock_id: str,
        limit: int,
        use_cache: bool
    ) -> List[dict]:
        """獲取台股新聞（含 TTL 快取）"""
        if use_cache:
            ttl_threshold = datetime.now() - timedelta(minutes=NEWS_CACHE_TTL_MINUTES)
            cached_news = db.query(StockNews).filter(
                StockNews.stock_id == stock_id,
                StockNews.fetched_at >= ttl_threshold
            ).order_by(StockNews.published_at.desc()).limit(limit).all()

            if cached_news:
                logger.info(f"使用快取新聞: {stock_id}, {len(cached_news)} 條")
                return [self._news_to_dict(n) for n in cached_news]

        # 從網路獲取新聞
        news_list = await news_fetcher.fetch_stock_news(stock_id, limit)

        # 進行情緒分析並儲存
        for news in news_list:
            sentiment_result = news_fetcher.analyze_sentiment_simple(
                news.get('title', ''),
                news.get('content', '')
            )
            news['sentiment'] = sentiment_result['sentiment']
            news['sentiment_score'] = sentiment_result['score']

            # 儲存到資料庫
            self._save_news(db, stock_id, news)

        return news_list

    async def get_news_sentiment_summary(self, db: Session, stock_id: str) -> Dict:
        """
        獲取新聞情感摘要 — 供綜合 AI 分析(F3)使用

        Returns:
            {
                'total': int,
                'positive': int,
                'negative': int,
                'neutral': int,
                'avg_score': float,
                'overall': str,
                'recent_titles': List[str]
            }
        """
        ttl_threshold = datetime.now() - timedelta(hours=6)
        recent_news = db.query(StockNews).filter(
            StockNews.stock_id == stock_id,
            StockNews.fetched_at >= ttl_threshold
        ).order_by(StockNews.published_at.desc()).limit(20).all()

        if not recent_news:
            # 即時抓取
            try:
                news_list = await news_fetcher.fetch_stock_news(stock_id, 10)
                for news in news_list:
                    sr = news_fetcher.analyze_sentiment_simple(news.get('title', ''))
                    news['sentiment'] = sr['sentiment']
                    news['sentiment_score'] = sr['score']
                    self._save_news(db, stock_id, news)

                recent_news = db.query(StockNews).filter(
                    StockNews.stock_id == stock_id,
                ).order_by(StockNews.published_at.desc()).limit(20).all()
            except Exception as e:
                logger.error(f"即時抓取新聞失敗: {e}")

        if not recent_news:
            return {'total': 0, 'positive': 0, 'negative': 0, 'neutral': 0,
                    'avg_score': 0, 'overall': 'neutral', 'recent_titles': []}

        positive = sum(1 for n in recent_news if n.sentiment == 'positive')
        negative = sum(1 for n in recent_news if n.sentiment == 'negative')
        neutral = len(recent_news) - positive - negative
        scores = []
        for n in recent_news:
            try:
                scores.append(float(n.sentiment_score or 0))
            except (ValueError, TypeError):
                scores.append(0)
        avg_score = sum(scores) / len(scores) if scores else 0

        if avg_score > 0.15:
            overall = 'positive'
        elif avg_score < -0.15:
            overall = 'negative'
        else:
            overall = 'neutral'

        return {
            'total': len(recent_news),
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'avg_score': round(avg_score, 2),
            'overall': overall,
            'recent_titles': [n.title for n in recent_news[:5]],
        }

    async def _get_us_stock_news(self, ticker: str, limit: int) -> List[dict]:
        """獲取美股新聞"""
        try:
            # 使用 global_news_fetcher (主要使用 yfinance API)
            news_list = global_news_fetcher.fetch_stock_news(ticker, limit)
            logger.info(f"Got {len(news_list)} news for US stock {ticker}")

            # 轉換格式以匹配前端期望
            formatted_news = []
            for news in news_list:
                formatted_news.append({
                    'id': news.get('url', ''),
                    'stock_id': ticker,
                    'title': news.get('title', ''),
                    'content': news.get('summary', ''),
                    'summary': news.get('summary', ''),
                    'source': news.get('source', 'Global News'),
                    'source_url': news.get('url', ''),
                    'sentiment': news.get('sentiment', 'neutral'),
                    'sentiment_score': news.get('sentiment_score', 0),
                    'published_at': news.get('published_at'),
                    'market_region': 'US',
                })

            return formatted_news
        except Exception as e:
            logger.error(f"US stock news fetch error: {e}")
            return []

    async def get_market_news(self, db: Session, limit: int = 20, market: str = "TW") -> List[dict]:
        """
        獲取市場新聞

        Args:
            db: 資料庫會話
            limit: 返回數量限制
            market: 市場 - "TW" (台股) 或 "US" (美股)

        Returns:
            新聞列表
        """
        if market == "US":
            # 美股市場新聞
            try:
                news_list = global_news_fetcher.fetch_market_news(limit)
                logger.info(f"Got {len(news_list)} market news for US")

                # 轉換格式
                formatted_news = []
                for news in news_list:
                    formatted_news.append({
                        'id': news.get('url', ''),
                        'title': news.get('title', ''),
                        'content': news.get('summary', ''),
                        'summary': news.get('summary', ''),
                        'source': news.get('source', 'Global News'),
                        'source_url': news.get('url', ''),
                        'sentiment': news.get('sentiment', 'neutral'),
                        'sentiment_score': news.get('sentiment_score', 0),
                        'published_at': news.get('published_at'),
                        'market_region': 'US',
                    })

                return formatted_news
            except Exception as e:
                logger.error(f"US market news fetch error: {e}")
                return []
        else:
            # 台股市場新聞
            news_list = await news_fetcher.fetch_market_news(limit)

            # 進行情緒分析
            for news in news_list:
                sentiment_result = news_fetcher.analyze_sentiment_simple(
                    news.get('title', ''),
                    news.get('content', '')
                )
                news['sentiment'] = sentiment_result['sentiment']
                news['sentiment_score'] = sentiment_result['score']

            return news_list

    def _save_news(self, db: Session, stock_id: str, news_data: dict) -> Optional[StockNews]:
        """儲存新聞到資料庫"""
        try:
            # 檢查是否已存在
            existing = db.query(StockNews).filter(
                StockNews.title == news_data.get('title'),
                StockNews.stock_id == stock_id
            ).first()

            if existing:
                return existing

            news = StockNews(
                stock_id=stock_id,
                title=news_data.get('title'),
                content=news_data.get('content'),
                summary=news_data.get('summary'),
                source=news_data.get('source'),
                source_url=news_data.get('source_url'),
                sentiment=news_data.get('sentiment'),
                sentiment_score=str(news_data.get('sentiment_score', 0)),
                published_at=news_data.get('published_at'),
            )
            db.add(news)
            db.commit()
            db.refresh(news)
            return news
        except Exception as e:
            db.rollback()
            logger.error(f"儲存新聞失敗: {e}")
            return None

    def _news_to_dict(self, news: StockNews) -> dict:
        """轉換新聞物件為字典"""
        return {
            'id': news.id,
            'stock_id': news.stock_id,
            'title': news.title,
            'content': news.content,
            'summary': news.summary,
            'source': news.source,
            'source_url': news.source_url,
            'sentiment': news.sentiment,
            'sentiment_score': float(news.sentiment_score) if news.sentiment_score else None,
            'published_at': news.published_at.isoformat() if news.published_at else None,
            'fetched_at': news.fetched_at.isoformat() if news.fetched_at else None,
        }


# 單例
news_service = NewsService()
