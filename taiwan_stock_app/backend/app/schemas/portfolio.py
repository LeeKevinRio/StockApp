"""
Portfolio Schemas
專業級高風險交易分析平台 - 投資組合數據模型
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class TransactionTypeEnum(str, Enum):
    """交易類型"""
    BUY = "buy"
    SELL = "sell"


# ==================== Portfolio ====================

class PortfolioCreate(BaseModel):
    """創建投資組合"""
    name: str
    description: Optional[str] = None
    initial_capital: float = 0


class PortfolioUpdate(BaseModel):
    """更新投資組合"""
    name: Optional[str] = None
    description: Optional[str] = None


class PortfolioResponse(BaseModel):
    """投資組合響應"""
    id: int
    user_id: int
    name: str
    description: Optional[str]
    initial_capital: float
    created_at: datetime
    updated_at: datetime
    # 計算欄位
    total_value: float = 0  # 總市值
    total_cost: float = 0  # 總成本
    total_pnl: float = 0  # 總損益
    total_pnl_percent: float = 0  # 總損益百分比
    positions_count: int = 0  # 持倉數量

    class Config:
        from_attributes = True


# ==================== Position ====================

class PositionResponse(BaseModel):
    """持倉響應"""
    id: int
    portfolio_id: int
    stock_id: str
    stock_name: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float = 0  # 市值
    unrealized_pnl: float
    unrealized_pnl_percent: float
    last_updated: datetime

    class Config:
        from_attributes = True


# ==================== Transaction ====================

class TransactionCreate(BaseModel):
    """創建交易"""
    stock_id: str
    stock_name: str
    transaction_type: TransactionTypeEnum
    quantity: int
    price: float
    fee: float = 0
    tax: float = 0
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None


class TransactionResponse(BaseModel):
    """交易響應"""
    id: int
    portfolio_id: int
    stock_id: str
    stock_name: str
    transaction_type: str
    quantity: int
    price: float
    fee: float
    tax: float
    total_amount: float
    notes: Optional[str]
    transaction_date: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== 統計摘要 ====================

class PortfolioSummary(BaseModel):
    """投資組合摘要"""
    total_value: float  # 總市值
    total_cost: float  # 總成本
    total_pnl: float  # 總損益
    total_pnl_percent: float  # 總損益百分比
    cash_balance: float  # 現金餘額
    positions_count: int  # 持倉數量
    winning_positions: int  # 獲利持倉
    losing_positions: int  # 虧損持倉
    best_performer: Optional[str] = None  # 最佳表現
    worst_performer: Optional[str] = None  # 最差表現


class PositionAllocation(BaseModel):
    """持倉配置"""
    stock_id: str
    stock_name: str
    market_value: float
    weight: float  # 佔比


class PortfolioPerformance(BaseModel):
    """投資組合績效"""
    daily_return: float
    weekly_return: float
    monthly_return: float
    total_return: float
    max_drawdown: float
    sharpe_ratio: float


# ==================== 列表響應 ====================

class PortfolioListResponse(BaseModel):
    """投資組合列表響應"""
    portfolios: List[PortfolioResponse]
    total: int


class PositionListResponse(BaseModel):
    """持倉列表響應"""
    positions: List[PositionResponse]
    total: int


class TransactionListResponse(BaseModel):
    """交易列表響應"""
    transactions: List[TransactionResponse]
    total: int
