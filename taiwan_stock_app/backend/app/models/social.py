"""
社群討論模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, Date, JSON
from sqlalchemy.sql import func

from app.database import Base


class SocialPost(Base):
    """社群貼文"""
    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(20), nullable=False, index=True)  # 'ptt', 'dcard'
    board = Column(String(50))  # 看板名稱

    title = Column(String(500), nullable=False)
    content = Column(Text)
    author = Column(String(100))
    url = Column(String(1000))

    # 提及的股票 (JSON array)
    mentioned_stocks = Column(JSON, default=[])

    # 情緒分析
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(Numeric(3, 2))  # -1.00 到 1.00

    # 互動數據
    push_count = Column(Integer, default=0)  # 推
    boo_count = Column(Integer, default=0)   # 噓
    comment_count = Column(Integer, default=0)

    # 時間
    posted_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<SocialPost {self.platform} {self.title[:30]}>"


class StockSentiment(Base):
    """股票每日情緒統計"""
    __tablename__ = "stock_sentiments"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)

    # 討論統計
    mention_count = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)

    # 綜合情緒分數 (-1.0 到 1.0)
    sentiment_score = Column(Numeric(3, 2))

    # 熱門程度 (與歷史平均相比)
    heat_level = Column(String(20))  # 'hot', 'normal', 'cold'

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<StockSentiment {self.stock_id} {self.date}>"
