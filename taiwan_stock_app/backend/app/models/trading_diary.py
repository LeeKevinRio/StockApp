"""
Trading Diary model - 交易日記
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class TradingDiaryEntry(Base):
    __tablename__ = "trading_diary"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id = Column(String(10), nullable=True)
    trade_date = Column(DateTime(timezone=True), server_default=func.now())
    trade_type = Column(String(10), nullable=True)  # 'buy', 'sell', 'watch', 'note'
    price = Column(Float, nullable=True)
    quantity = Column(Integer, nullable=True)
    pnl = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    emotion = Column(String(20), nullable=True)  # 'confident', 'anxious', 'calm', 'greedy', 'fearful'
    strategy = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    lesson_learned = Column(Text, nullable=True)
    tags = Column(String(200), nullable=True)  # comma-separated tags
    rating = Column(Integer, nullable=True)  # 1-5 self-rating
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
