"""
模擬交易模型
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class OrderType(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class VirtualAccount(Base):
    """虛擬交易帳戶"""
    __tablename__ = "virtual_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)

    # 資金
    initial_balance = Column(Numeric(15, 2), default=1000000)  # 初始資金 100萬
    cash_balance = Column(Numeric(15, 2), default=1000000)     # 現金餘額
    total_value = Column(Numeric(15, 2), default=1000000)      # 總資產價值

    # 損益
    total_profit_loss = Column(Numeric(15, 2), default=0)      # 總損益
    total_profit_loss_percent = Column(Numeric(6, 4), default=0)  # 總損益百分比

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    user = relationship("User", backref="virtual_account")
    positions = relationship("VirtualPosition", back_populates="account", cascade="all, delete-orphan")
    orders = relationship("VirtualOrder", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<VirtualAccount user_id={self.user_id} balance={self.cash_balance}>"


class VirtualPosition(Base):
    """虛擬持倉"""
    __tablename__ = "virtual_positions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('virtual_accounts.id', ondelete='CASCADE'), nullable=False)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False)

    # 持倉資訊
    quantity = Column(Integer, default=0)              # 持有股數
    avg_cost = Column(Numeric(10, 2))                  # 平均成本
    current_price = Column(Numeric(10, 2))             # 當前價格
    market_value = Column(Numeric(15, 2))              # 市值

    # 損益
    unrealized_pnl = Column(Numeric(15, 2), default=0)       # 未實現損益
    unrealized_pnl_percent = Column(Numeric(6, 4), default=0)  # 未實現損益百分比

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # 關聯
    account = relationship("VirtualAccount", back_populates="positions")
    stock = relationship("Stock")

    def __repr__(self):
        return f"<VirtualPosition {self.stock_id} qty={self.quantity}>"


class VirtualOrder(Base):
    """虛擬訂單"""
    __tablename__ = "virtual_orders"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey('virtual_accounts.id', ondelete='CASCADE'), nullable=False)
    stock_id = Column(String(10), ForeignKey('stocks.stock_id'), nullable=False)

    # 訂單資訊
    order_type = Column(String(10), nullable=False)    # BUY, SELL
    quantity = Column(Integer, nullable=False)          # 委託數量
    price = Column(Numeric(10, 2), nullable=False)     # 委託價格
    filled_quantity = Column(Integer, default=0)       # 成交數量
    filled_price = Column(Numeric(10, 2))              # 成交價格

    # 狀態
    status = Column(String(20), default='PENDING')     # PENDING, FILLED, CANCELLED, FAILED

    # 時間戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    filled_at = Column(DateTime(timezone=True))

    # 關聯
    account = relationship("VirtualAccount", back_populates="orders")
    stock = relationship("Stock")

    def __repr__(self):
        return f"<VirtualOrder {self.order_type} {self.stock_id} qty={self.quantity}>"
