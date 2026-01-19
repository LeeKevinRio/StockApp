"""
AI Report and Chat History models
"""
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.database import Base


class AIReport(Base):
    __tablename__ = "ai_reports"
    __table_args__ = (UniqueConstraint('stock_id', 'user_id', 'report_date', name='uix_ai_report'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    report_date = Column(Date, nullable=False, index=True)
    suggestion = Column(String(10), nullable=False)  # 'BUY', 'SELL', 'HOLD'
    confidence = Column(Numeric(3, 2))  # 0.00 ~ 1.00
    target_price = Column(Numeric(10, 2))
    stop_loss_price = Column(Numeric(10, 2))
    reasoning = Column(Text, nullable=False)
    key_factors = Column(JSONB)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AIChatHistory(Base):
    __tablename__ = "ai_chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'))
    role = Column(String(10), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
