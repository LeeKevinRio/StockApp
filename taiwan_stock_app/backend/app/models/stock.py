"""
Stock related models
"""
from sqlalchemy import Column, String, Integer, Date, DateTime, BigInteger, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    stock_id = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    english_name = Column(String(200))
    industry = Column(String(100))
    market = Column(String(10), nullable=False)  # 'TWSE', 'TPEx', 'NYSE', 'NASDAQ', etc.
    market_region = Column(String(5), nullable=False, default='TW', index=True)  # 'TW' or 'US'
    sector = Column(String(100))  # Sector for US stocks
    listed_date = Column(Date)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class StockPrice(Base):
    __tablename__ = "stock_prices"
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uix_stock_date'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    open = Column(Numeric(10, 2))
    high = Column(Numeric(10, 2))
    low = Column(Numeric(10, 2))
    close = Column(Numeric(10, 2))
    volume = Column(BigInteger)
    change_percent = Column(Numeric(6, 2))


class StockChip(Base):
    __tablename__ = "stock_chips"
    __table_args__ = (UniqueConstraint('stock_id', 'date', name='uix_chip_stock_date'),)

    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    foreign_buy = Column(BigInteger)  # 外資買賣超
    investment_trust_buy = Column(BigInteger)  # 投信買賣超
    dealer_buy = Column(BigInteger)  # 自營商買賣超
    margin_balance = Column(BigInteger)  # 融資餘額
    short_balance = Column(BigInteger)  # 融券餘額
