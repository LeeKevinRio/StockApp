"""
Watchlist model + Watchlist Group model
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class WatchlistGroup(Base):
    __tablename__ = "watchlist_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(10), default="#2196F3")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint('user_id', 'stock_id', name='uix_user_stock'),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False)
    group_id = Column(Integer, ForeignKey('watchlist_groups.id', ondelete='SET NULL'), nullable=True)
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text)
    alert_price_high = Column(Numeric(10, 2))
    alert_price_low = Column(Numeric(10, 2))
