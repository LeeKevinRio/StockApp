"""
Backtest router
專業級高風險交易分析平台 - 回測績效 API
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional

from app.models import User
from app.schemas.backtest import (
    PerformanceReport,
    PerformanceStats,
    SuggestionRecord,
    SuggestionRecordList,
    RecordSuggestionRequest,
    UpdateResultRequest,
)
from app.services.backtest_service import BacktestService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/backtest", tags=["backtest"])
backtest_service = BacktestService()


@router.get("/performance", response_model=PerformanceReport)
async def get_performance_report(
    current_user: User = Depends(get_current_user),
):
    """
    取得完整績效報告

    包含：
    - 總體績效統計
    - 按建議類型分析
    - 按信心度分析
    - 按產業分析
    - 準確率趨勢
    """
    report = backtest_service.generate_performance_report()
    return report


@router.get("/performance/summary")
async def get_performance_summary(
    current_user: User = Depends(get_current_user),
):
    """取得績效摘要"""
    stats = backtest_service.calculate_performance()
    return {
        "total_trades": stats.total_trades,
        "win_rate": round(stats.win_rate, 1),
        "avg_return": round(stats.avg_return, 2),
        "profit_factor": round(stats.profit_factor, 2),
        "sharpe_ratio": round(stats.sharpe_ratio, 2),
        "winning_trades": stats.winning_trades,
        "losing_trades": stats.losing_trades,
    }


@router.get("/records", response_model=SuggestionRecordList)
async def get_suggestion_records(
    limit: int = 50,
    suggestion: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """
    取得建議記錄列表

    Args:
        limit: 數量限制
        suggestion: 篩選建議類型 (BUY/SELL/HOLD)
    """
    records = backtest_service.get_recent_records(limit, suggestion)
    return SuggestionRecordList(
        records=[
            SuggestionRecord(**backtest_service.record_to_dict(r))
            for r in records
        ],
        total=len(records),
    )


@router.post("/records", response_model=SuggestionRecord)
async def record_suggestion(
    request: RecordSuggestionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    記錄 AI 建議

    當 AI 生成建議時，記錄進場價、目標價、停損價等資訊，
    以便後續追蹤準確率。
    """
    record = backtest_service.record_suggestion(
        stock_id=request.stock_id,
        stock_name=request.stock_name,
        suggestion=request.suggestion,
        confidence=request.confidence,
        entry_price=request.entry_price,
        target_price=request.target_price,
        stop_loss=request.stop_loss,
        industry=request.industry,
    )
    return SuggestionRecord(**backtest_service.record_to_dict(record))


@router.put("/records/{record_id}", response_model=SuggestionRecord)
async def update_result(
    record_id: str,
    request: UpdateResultRequest,
    current_user: User = Depends(get_current_user),
):
    """
    更新交易結果

    當交易結束時，記錄出場價以計算實際報酬率。
    """
    record = backtest_service.update_result(record_id, request.exit_price)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return SuggestionRecord(**backtest_service.record_to_dict(record))


@router.get("/accuracy-trend")
async def get_accuracy_trend(
    days: int = 30,
    current_user: User = Depends(get_current_user),
):
    """取得準確率趨勢"""
    trend = backtest_service.get_accuracy_trend(days)
    return {"trend": trend, "days": days}


@router.get("/by-suggestion")
async def get_performance_by_suggestion(
    current_user: User = Depends(get_current_user),
):
    """按建議類型分析績效"""
    result = backtest_service.get_performance_by_suggestion()
    return {
        k: backtest_service._stats_to_dict(v)
        for k, v in result.items()
    }


@router.get("/by-confidence")
async def get_performance_by_confidence(
    current_user: User = Depends(get_current_user),
):
    """按信心度分析績效"""
    result = backtest_service.get_performance_by_confidence()
    return {
        k: backtest_service._stats_to_dict(v)
        for k, v in result.items()
    }


@router.get("/by-industry")
async def get_performance_by_industry(
    current_user: User = Depends(get_current_user),
):
    """按產業分析績效"""
    result = backtest_service.get_performance_by_industry()
    return {
        k: backtest_service._stats_to_dict(v)
        for k, v in result.items()
    }
