"""
Portfolio Models
專業級高風險交易分析平台 - 投資組合數據模型
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class TransactionType(enum.Enum):
    """交易類型"""
    BUY = "buy"
    SELL = "sell"


class Portfolio(Base):
    """投資組合"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500), nullable=True)
    initial_capital = Column(Float, default=0)  # 初始資金
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")


class Position(Base):
    """持倉"""
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(String(10), nullable=False)
    stock_name = Column(String(100), nullable=False)
    quantity = Column(Integer, default=0)  # 持有數量（股）
    avg_cost = Column(Float, default=0)  # 平均成本
    current_price = Column(Float, default=0)  # 當前價格
    unrealized_pnl = Column(Float, default=0)  # 未實現損益
    unrealized_pnl_percent = Column(Float, default=0)  # 未實現損益百分比
    last_updated = Column(DateTime, default=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")


class Transaction(Base):
    """交易記錄"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(String(10), nullable=False)
    stock_name = Column(String(100), nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    quantity = Column(Integer, nullable=False)  # 交易數量（股）
    price = Column(Float, nullable=False)  # 成交價
    fee = Column(Float, default=0)  # 手續費
    tax = Column(Float, default=0)  # 交易稅
    total_amount = Column(Float, nullable=False)  # 總金額
    notes = Column(String(500), nullable=True)  # 備註
    transaction_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
