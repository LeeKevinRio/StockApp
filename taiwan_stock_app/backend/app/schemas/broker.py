"""
Broker Schemas — 券商連動 API 請求/回應模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ==================== 請求 ====================

class LinkAccountRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)
    pin: str = Field(..., min_length=4, max_length=10)


class Verify2FARequest(BaseModel):
    account_id: int
    code: str = Field(..., min_length=4, max_length=10)


# ==================== 回應 ====================

class LinkAccountResponse(BaseModel):
    account_id: int
    status: str  # "active" | "needs_2fa" | "error"
    message: str


class BrokerStatusResponse(BaseModel):
    linked: bool
    broker_type: Optional[str] = None
    status: Optional[str] = None
    account_number: Optional[str] = None
    last_synced: Optional[datetime] = None


class BrokerPositionResponse(BaseModel):
    symbol: str
    quantity: float
    avg_cost: float
    market_value: float
    unrealized_pnl: float
    last_updated: Optional[datetime] = None

    model_config = {"from_attributes": True}


class BrokerPositionListResponse(BaseModel):
    positions: List[BrokerPositionResponse]
    total: int
