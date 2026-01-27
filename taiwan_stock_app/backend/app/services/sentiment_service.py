"""
社群情緒分析服務 - 支援 PTT, Dcard, Mobile01
"""
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import logging

from app.models.social import SocialPost, StockSentiment
from app.data_fetchers.taiwan_social_fetcher import taiwan_social_fetcher

logger = logging.getLogger(__name__)


class SentimentService:
    """社群情緒分析服務 - 支援多平台"""

    async def get_stock_sentiment(
        self,
        db: Session,
        stock_id: str,
        days: int = 7
    ) -> Dict:
        """
        獲取個股社群情緒分析

        Args:
            db: 資料庫會話
            stock_id: 股票代碼
            days: 分析天數

        Returns:
            情緒分析結果
        """
        # 從多平台獲取相關討論 (PTT, Dcard, Mobile01)
        try:
            posts = taiwan_social_fetcher.fetch_stock_discussions(stock_id, limit=30)
            logger.info(f"Found {len(posts)} posts mentioning {stock_id}")
        except Exception as e:
            logger.error(f"Error fetching social posts: {e}")
            posts = []

        # 統計情緒
        positive_count = sum(1 for p in posts if p.get('sentiment') == 'positive')
        negative_count = sum(1 for p in posts if p.get('sentiment') == 'negative')
        neutral_count = sum(1 for p in posts if p.get('sentiment') == 'neutral')
        total = len(posts)

        # 計算情緒分數
        scores = [p.get('sentiment_score', 0) for p in posts if p.get('sentiment_score') is not None]
        avg_score = sum(scores) / len(scores) if scores else 0

        # 判斷整體情緒
        if avg_score > 0.15:
            overall_sentiment = 'positive'
        elif avg_score < -0.15:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'

        # 儲存情緒數據
        self._save_sentiment(db, stock_id, {
            'mention_count': total,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'neutral_count': neutral_count,
            'sentiment_score': avg_score,
        })

        return {
            'stock_id': stock_id,
            'total_mentions': total,
            'sentiment_summary': {
                'positive': positive_count,
                'negative': negative_count,
                'neutral': neutral_count,
                'score': round(avg_score, 2),
                'overall': overall_sentiment,
            },
            'recent_posts': posts[:10],
            'sentiment_trend': await self._get_sentiment_trend(db, stock_id, days),
        }

    async def get_hot_stocks(self, db: Session, limit: int = 10) -> List[Dict]:
        """
        獲取熱門討論股票 (PTT, Dcard, Mobile01)

        Args:
            db: 資料庫會話
            limit: 返回數量

        Returns:
            熱門股票列表
        """
        try:
            hot_stocks = taiwan_social_fetcher.get_hot_stocks(limit)

            # 補充股票名稱
            for stock in hot_stocks:
                stock['stock_name'] = self._get_stock_name(db, stock['stock_id'])

            return hot_stocks
        except Exception as e:
            logger.error(f"Error fetching hot stocks: {e}")
            return []

    async def get_market_sentiment(self, db: Session) -> Dict:
        """
        獲取市場整體情緒

        Returns:
            市場情緒分析
        """
        # 獲取最新貼文 (從多平台)
        try:
            posts = taiwan_social_fetcher.fetch_all_platforms(limit_per_platform=20)
        except Exception as e:
            logger.error(f"Error fetching market posts: {e}")
            posts = []

        # 統計整體情緒
        positive_count = sum(1 for p in posts if p.get('sentiment') == 'positive')
        negative_count = sum(1 for p in posts if p.get('sentiment') == 'negative')
        total = len(posts)

        if total == 0:
            sentiment_ratio = 0.5
        else:
            sentiment_ratio = positive_count / total

        # 判斷市場情緒
        if sentiment_ratio > 0.6:
            market_sentiment = 'bullish'
            description = '市場氣氛樂觀，多頭聲音較多'
        elif sentiment_ratio < 0.4:
            market_sentiment = 'bearish'
            description = '市場氣氛悲觀，空頭聲音較多'
        else:
            market_sentiment = 'neutral'
            description = '市場氣氛中性，多空分歧'

        return {
            'total_posts': total,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'sentiment_ratio': round(sentiment_ratio, 2),
            'market_sentiment': market_sentiment,
            'description': description,
            'updated_at': datetime.now().isoformat(),
        }

    def _save_sentiment(self, db: Session, stock_id: str, data: Dict):
        """儲存情緒數據到資料庫"""
        try:
            today = date.today()
            existing = db.query(StockSentiment).filter(
                StockSentiment.stock_id == stock_id,
                StockSentiment.date == today
            ).first()

            if existing:
                existing.mention_count = data['mention_count']
                existing.positive_count = data['positive_count']
                existing.negative_count = data['negative_count']
                existing.neutral_count = data['neutral_count']
                existing.sentiment_score = data['sentiment_score']
            else:
                sentiment = StockSentiment(
                    stock_id=stock_id,
                    date=today,
                    mention_count=data['mention_count'],
                    positive_count=data['positive_count'],
                    negative_count=data['negative_count'],
                    neutral_count=data['neutral_count'],
                    sentiment_score=data['sentiment_score'],
                )
                db.add(sentiment)

            db.commit()
        except Exception as e:
            db.rollback()
            print(f"儲存情緒數據失敗: {e}")

    async def _get_sentiment_trend(self, db: Session, stock_id: str, days: int) -> List[Dict]:
        """獲取情緒趨勢"""
        start_date = date.today() - timedelta(days=days)

        sentiments = db.query(StockSentiment).filter(
            StockSentiment.stock_id == stock_id,
            StockSentiment.date >= start_date
        ).order_by(StockSentiment.date).all()

        return [
            {
                'date': s.date.isoformat(),
                'mention_count': s.mention_count,
                'positive_count': s.positive_count,
                'negative_count': s.negative_count,
                'sentiment_score': float(s.sentiment_score) if s.sentiment_score else 0,
            }
            for s in sentiments
        ]

    def _get_stock_name(self, db: Session, stock_id: str) -> Optional[str]:
        """從資料庫獲取股票名稱"""
        from app.models import Stock
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        return stock.name if stock else None


# 單例
sentiment_service = SentimentService()

