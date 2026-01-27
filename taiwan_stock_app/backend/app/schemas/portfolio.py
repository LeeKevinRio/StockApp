"""
Portfolio Schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


class PortfolioHoldingBase(BaseModel):
    """持股基礎 Schema"""
    stock_id: str
    quantity: int
    avg_cost: Decimal
    buy_date: date
    notes: Optional[str] = None


class PortfolioHoldingCreate(PortfolioHoldingBase):
    """建立持股"""
    pass


class PortfolioHoldingUpdate(BaseModel):
    """更新持股"""
    quantity: Optional[int] = None
    avg_cost: Optional[Decimal] = None
    notes: Optional[str] = None


class PortfolioHoldingResponse(PortfolioHoldingBase):
    """持股回應"""
    id: int
    portfolio_id: int
    stock_name: Optional[str] = None
    current_price: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    unrealized_pnl: Optional[Decimal] = None
    unrealized_pnl_percent: Optional[Decimal] = None
    created_at: datetime

    class Config:
        from_attributes = True


class PortfolioBase(BaseModel):
    """組合基礎 Schema"""
    name: str
    description: Optional[str] = None


class PortfolioCreate(PortfolioBase):
    """建立組合"""
    is_default: bool = False


class PortfolioUpdate(BaseModel):
    """更新組合"""
    name: Optional[str] = None
    description: Optional[str] = None


class PortfolioResponse(PortfolioBase):
    """組合回應"""
    id: int
    user_id: int
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioSummary(BaseModel):
    """組合摘要"""
    id: int
    name: str
    total_cost: Decimal
    total_value: Decimal
    total_pnl: Decimal
    total_pnl_percent: Decimal
    holdings_count: int


class PortfolioDetailResponse(PortfolioResponse):
    """組合詳情回應"""
    holdings: List[PortfolioHoldingResponse]
    total_cost: Decimal
    total_value: Decimal
    total_pnl: Decimal
    total_pnl_percent: Decimal


class PortfolioSnapshotResponse(BaseModel):
    """組合快照回應"""
    date: date
    total_value: Decimal
    total_cost: Decimal
    daily_return: Optional[Decimal]
    total_return: Optional[Decimal]

    class Config:
        from_attributes = True


class PortfolioPerformance(BaseModel):
    """組合績效"""
    portfolio_id: int
    portfolio_name: str
    period_days: int
    start_value: Decimal
    end_value: Decimal
    absolute_return: Decimal
    percent_return: Decimal
    benchmark_return: Optional[Decimal] = None  # 大盤報酬率
    alpha: Optional[Decimal] = None  # 超額報酬
    snapshots: List[PortfolioSnapshotResponse]


class PortfolioAllocation(BaseModel):
    """持股配置"""
    stock_id: str
    stock_name: str
    market_value: Decimal
    weight: Decimal  # 佔比


class PortfolioAllocationResponse(BaseModel):
    """持股配置回應"""
    portfolio_id: int
    portfolio_name: str
    total_value: Decimal
    allocations: List[PortfolioAllocation]
