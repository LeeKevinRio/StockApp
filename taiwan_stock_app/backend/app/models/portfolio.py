"""
Portfolio Models
"""
from sqlalchemy import Column, Integer, String, Numeric, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base


class Portfolio(Base):
    """投資組合"""
    __tablename__ = "portfolios"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    snapshots = relationship("PortfolioSnapshot", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioHolding(Base):
    """投資組合持股"""
    __tablename__ = "portfolio_holdings"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    stock_id = Column(String(10), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_cost = Column(Numeric(10, 2), nullable=False)
    buy_date = Column(Date, nullable=False)
    notes = Column(String(500))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")


class PortfolioSnapshot(Base):
    """投資組合每日快照"""
    __tablename__ = "portfolio_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    date = Column(Date, nullable=False)
    total_value = Column(Numeric(15, 2), nullable=False)
    total_cost = Column(Numeric(15, 2), nullable=False)
    daily_return = Column(Numeric(8, 4))  # 日報酬率
    total_return = Column(Numeric(8, 4))  # 總報酬率
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    portfolio = relationship("Portfolio", back_populates="snapshots")
