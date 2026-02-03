"""
新聞模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class StockNews(Base):
    """股票新聞"""
    __tablename__ = "stock_news"

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=True, index=True)

    title = Column(String(500), nullable=False)
    content = Column(Text)
    summary = Column(Text)  # AI 生成的摘要

    source = Column(String(100))  # 來源: yahoo, cnyes, moneydj 等
    source_url = Column(String(1000))

    # 情緒分析
    sentiment = Column(String(20))  # positive, negative, neutral
    sentiment_score = Column(String(10))  # -1.0 到 1.0

    # 時間
    published_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())

    # 關聯
    stock = relationship("Stock", backref="news")

    def __repr__(self):
        return f"<StockNews {self.id} {self.title[:30]}>"
