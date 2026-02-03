"""
Backtest Schemas
專業級高風險交易分析平台 - 回測績效數據模型
"""

from typing import Dict, List, Optional
from pydantic import BaseModel


class PerformanceStats(BaseModel):
    """績效統計"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    break_even_trades: int
    pending_trades: int
    win_rate: float
    avg_return: float
    max_return: float
    min_return: float
    avg_holding_days: float
    profit_factor: float
    sharpe_ratio: float


class PerformanceSummary(BaseModel):
    """績效摘要"""
    total_trades: int
    win_rate: float
    avg_return: float
    profit_factor: float
    sharpe_ratio: float


class AccuracyTrend(BaseModel):
    """準確率趨勢"""
    date: str
    total: int
    wins: int
    accuracy: float


class PerformanceReport(BaseModel):
    """績效報告"""
    generated_at: str
    summary: PerformanceSummary
    overall: PerformanceStats
    by_suggestion: Dict[str, PerformanceStats]
    by_confidence: Dict[str, PerformanceStats]
    by_industry: Dict[str, PerformanceStats]
    accuracy_trend: List[AccuracyTrend]


class SuggestionRecord(BaseModel):
    """建議記錄"""
    id: str
    stock_id: str
    stock_name: str
    suggestion: str
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    report_date: str
    industry: Optional[str] = None
    actual_result: Optional[str] = None
    exit_price: Optional[float] = None
    exit_date: Optional[str] = None
    return_percent: Optional[float] = None
    holding_days: Optional[int] = None


class RecordSuggestionRequest(BaseModel):
    """記錄建議請求"""
    stock_id: str
    stock_name: str
    suggestion: str
    confidence: float
    entry_price: float
    target_price: float
    stop_loss: float
    industry: Optional[str] = None


class UpdateResultRequest(BaseModel):
    """更新結果請求"""
    exit_price: float


class SuggestionRecordList(BaseModel):
    """建議記錄列表"""
    records: List[SuggestionRecord]
    total: int
