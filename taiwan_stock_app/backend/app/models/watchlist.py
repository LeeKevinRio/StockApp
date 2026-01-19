"""
Watchlist model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint('user_id', 'stock_id', name='uix_user_stock'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    alert_price_high = Column(Numeric(10, 2))
    alert_price_low = Column(Numeric(10, 2))
