"""
策略回測 API Schema
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class BacktestRequest(BaseModel):
    """回測請求"""
    stock_id: str = Field(..., description="股票代碼")
    market: str = Field(default="TW", description="市場 (TW / US)")
    strategy: str = Field(..., description="策略名稱")
    params: Dict[str, Any] = Field(default_factory=dict, description="策略參數")
    start_date: str = Field(..., description="起始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="結束日期 YYYY-MM-DD")
    initial_capital: float = Field(default=1000000, description="初始資金")


class TradeRecord(BaseModel):
    """單筆交易紀錄"""
    entry_date: str
    entry_price: float
    exit_date: str
    exit_price: float
    shares: int = 0
    pnl: float
    return_pct: float
    holding_days: int


class EquityPoint(BaseModel):
    """權益曲線資料點"""
    date: str
    equity: float
    drawdown: float


class SignalRecord(BaseModel):
    """交易信號紀錄"""
    date: str
    signal: str
    price: float
    indicator_value: str


class PerformanceMetrics(BaseModel):
    """績效指標"""
    total_return: float = Field(description="總報酬率 %")
    annualized_return: float = Field(description="年化報酬率 %")
    max_drawdown: float = Field(description="最大回撤 %")
    sharpe_ratio: float = Field(description="Sharpe Ratio")
    win_rate: float = Field(description="勝率 %")
    profit_factor: float = Field(description="獲利因子")
    total_trades: int = Field(description="交易次數")
    avg_holding_days: float = Field(description="平均持倉天數")


class BacktestResult(BaseModel):
    """回測結果"""
    stock_id: str
    stock_name: str = ""
    strategy: str
    params: Dict[str, Any]
    metrics: PerformanceMetrics
    equity_curve: List[EquityPoint]
    trades: List[TradeRecord]
    signals: List[SignalRecord]


class StrategyInfo(BaseModel):
    """策略資訊"""
    name: str
    display_name: str
    description: str
    default_params: Dict[str, Any]


class StrategyListResponse(BaseModel):
    """策略列表回應"""
    strategies: List[StrategyInfo]
