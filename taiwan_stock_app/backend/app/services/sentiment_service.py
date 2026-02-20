"""
社群情緒分析服務 - 支援 PTT, Dcard, Mobile01
"""
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from sqlalchemy.orm import Session
import logging

from sqlalchemy import cast, String
from app.models.social import SocialPost, StockSentiment
from app.data_fetchers.taiwan_social_fetcher import taiwan_social_fetcher

logger = logging.getLogger(__name__)


class SentimentService:
    """社群情緒分析服務 - 支援多平台"""

    # 社群快取 TTL（2 小時）
    SOCIAL_CACHE_TTL_HOURS = 2

    async def get_stock_sentiment(
        self,
        db: Session,
        stock_id: str,
        days: int = 7
    ) -> Dict:
        """
        獲取個股社群情緒分析（先查 DB 快取）

        Args:
            db: 資料庫會話
            stock_id: 股票代碼
            days: 分析天數

        Returns:
            情緒分析結果
        """
        # 先查 DB 快取（2 小時內有效）
        cache_threshold = datetime.now() - timedelta(hours=self.SOCIAL_CACHE_TTL_HOURS)
        cached_posts = db.query(SocialPost).filter(
            cast(SocialPost.mentioned_stocks, String).like(f'%"{stock_id}"%'),
            SocialPost.fetched_at >= cache_threshold
        ).order_by(SocialPost.posted_at.desc()).limit(30).all()

        if cached_posts:
            logger.info(f"使用快取社群貼文: {stock_id}, {len(cached_posts)} 條")
            posts = [self._social_post_to_dict(p) for p in cached_posts]
        else:
            # 從多平台獲取相關討論 (PTT, Dcard, Mobile01)
            try:
                posts = taiwan_social_fetcher.fetch_stock_discussions(stock_id, limit=30)
                logger.info(f"Found {len(posts)} posts mentioning {stock_id}")
                # 持久化到 DB
                self._save_social_posts(db, posts)
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

        # 儲存每日情緒摘要
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

    async def get_social_sentiment_for_ai(self, db: Session, stock_id: str) -> Dict:
        """
        獲取社群情緒摘要 — 供 F3 綜合 AI 分析使用

        Returns:
            {
                'total_mentions': int,
                'positive': int,
                'negative': int,
                'neutral': int,
                'avg_score': float,
                'overall': str,
                'top_topics': List[str],
                'platforms': List[str],
            }
        """
        # 先查近期 DB 數據
        cache_threshold = datetime.now() - timedelta(hours=6)
        cached_posts = db.query(SocialPost).filter(
            cast(SocialPost.mentioned_stocks, String).like(f'%"{stock_id}"%'),
            SocialPost.fetched_at >= cache_threshold
        ).order_by(SocialPost.posted_at.desc()).limit(30).all()

        if not cached_posts:
            # 即時抓取
            try:
                posts_data = taiwan_social_fetcher.fetch_stock_discussions(stock_id, limit=20)
                self._save_social_posts(db, posts_data)
                cached_posts = db.query(SocialPost).filter(
                    cast(SocialPost.mentioned_stocks, String).like(f'%"{stock_id}"%'),
                ).order_by(SocialPost.posted_at.desc()).limit(30).all()
            except Exception as e:
                logger.error(f"即時抓取社群數據失敗: {e}")

        if not cached_posts:
            return {
                'total_mentions': 0, 'positive': 0, 'negative': 0, 'neutral': 0,
                'avg_score': 0.0, 'overall': 'neutral', 'top_topics': [], 'platforms': [],
            }

        positive = sum(1 for p in cached_posts if p.sentiment == 'positive')
        negative = sum(1 for p in cached_posts if p.sentiment == 'negative')
        neutral = len(cached_posts) - positive - negative
        scores = []
        for p in cached_posts:
            try:
                scores.append(float(p.sentiment_score or 0))
            except (ValueError, TypeError):
                scores.append(0)
        avg_score = sum(scores) / len(scores) if scores else 0

        overall = 'positive' if avg_score > 0.15 else ('negative' if avg_score < -0.15 else 'neutral')
        platforms = list(set(p.platform for p in cached_posts if p.platform))

        return {
            'total_mentions': len(cached_posts),
            'positive': positive,
            'negative': negative,
            'neutral': neutral,
            'avg_score': round(avg_score, 2),
            'overall': overall,
            'top_topics': [p.title for p in cached_posts[:5]],
            'platforms': platforms,
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

    def _save_social_posts(self, db: Session, posts: List[Dict]):
        """持久化社群貼文到 social_posts 表"""
        saved = 0
        for post_data in posts:
            try:
                title = post_data.get('title', '')
                platform = post_data.get('platform', '')
                if not title or not platform:
                    continue

                # 檢查是否已存在（用 title + platform 去重）
                existing = db.query(SocialPost).filter(
                    SocialPost.title == title,
                    SocialPost.platform == platform,
                ).first()
                if existing:
                    continue

                mentioned = post_data.get('mentioned_stocks', [])
                if not isinstance(mentioned, list):
                    mentioned = [str(mentioned)] if mentioned else []

                posted_at = None
                if post_data.get('posted_at'):
                    try:
                        posted_at = datetime.fromisoformat(str(post_data['posted_at']).replace('Z', '+00:00'))
                    except Exception as e:
                        logger.warning(f"解析貼文時間失敗: {e}")

                social_post = SocialPost(
                    platform=platform,
                    board=post_data.get('board'),
                    title=title,
                    content=post_data.get('content', ''),
                    author=post_data.get('author'),
                    url=post_data.get('url'),
                    mentioned_stocks=mentioned,
                    sentiment=post_data.get('sentiment'),
                    sentiment_score=str(post_data.get('sentiment_score', 0)),
                    push_count=post_data.get('push_count', 0),
                    boo_count=post_data.get('boo_count', 0),
                    comment_count=post_data.get('comment_count', 0),
                    posted_at=posted_at,
                )
                db.add(social_post)
                saved += 1
            except Exception as e:
                logger.error(f"儲存社群貼文失敗: {e}")
                continue

        try:
            db.commit()
            if saved > 0:
                logger.info(f"儲存 {saved} 條社群貼文")
        except Exception as e:
            db.rollback()
            logger.error(f"批次儲存社群貼文失敗: {e}")

    def _social_post_to_dict(self, post: SocialPost) -> Dict:
        """轉換 SocialPost ORM 物件為字典"""
        mentioned = post.mentioned_stocks if isinstance(post.mentioned_stocks, list) else []
        return {
            'id': str(post.id) if post.id else '',
            'platform': post.platform,
            'board': post.board,
            'title': post.title,
            'content': post.content,
            'author': post.author,
            'url': post.url,
            'mentioned_stocks': mentioned,
            'sentiment': post.sentiment,
            'sentiment_score': float(post.sentiment_score) if post.sentiment_score else 0,
            'push_count': post.push_count or 0,
            'boo_count': post.boo_count or 0,
            'comment_count': post.comment_count or 0,
            'posted_at': post.posted_at.isoformat() if post.posted_at else None,
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
            logger.error(f"儲存情緒數據失敗: {e}")

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

