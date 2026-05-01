"""
Predictions Router - AI 預測追蹤 API
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, timedelta

logger = logging.getLogger(__name__)

from app.database import get_db
from app.models import User
from app.services.prediction_tracker import PredictionTracker
from app.services.trading_calendar import get_previous_trading_date
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/predictions", tags=["predictions"])
tracker = PredictionTracker()


@router.get("/statistics")
def get_prediction_statistics(
    days: int = Query(30, ge=1, le=365, description="統計天數"),
    market: Optional[str] = Query(None, description="市場過濾: TW or US"),
    stock_id: Optional[str] = Query(None, description="特定股票代碼"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    獲取 AI 預測準確度統計

    Returns:
        - total_predictions: 總預測數
        - direction_accuracy: 方向準確率 %
        - within_range_rate: 收盤價落在預測區間內的比率 %
        - avg_error_percent: 平均預測誤差 %
        - records: 最近預測詳情
    """
    # 自動更新尚未驗證的預測結果
    try:
        tracker.update_actual_results(db=db, market=market)
    except Exception as e:
        logger.warning(f"Auto-update prediction results failed: {e}")

    return tracker.get_accuracy_statistics(
        db=db,
        days=days,
        market=market,
        stock_id=stock_id
    )


@router.get("/daily/{target_date}")
def get_daily_predictions(
    target_date: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    獲取特定日期的預測摘要

    Args:
        target_date: 目標日期 (YYYY-MM-DD)
    """
    try:
        dt = date.fromisoformat(target_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    return tracker.get_daily_summary(db=db, target_date=dt)


@router.get("/yesterday")
def get_yesterday_predictions(
    market: Optional[str] = Query(None, description="市場過濾: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    獲取昨日預測與實際結果比較
    """
    # 自動更新尚未驗證的預測結果
    try:
        tracker.update_actual_results(db=db, market=market)
    except Exception as e:
        logger.warning(f"Auto-update prediction results failed: {e}")

    yesterday = get_previous_trading_date()

    return tracker.get_daily_summary(db=db, target_date=yesterday, market=market)


@router.post("/update-results")
def manually_update_results(
    market: Optional[str] = Query(None, description="市場: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    手動觸發更新預測的實際結果（通常由排程自動執行）
    """
    updated = tracker.update_actual_results(db=db, market=market)
    return {
        "message": f"Updated {updated} prediction records",
        "updated_count": updated
    }


@router.get("/stock/{stock_id}")
def get_stock_predictions(
    stock_id: str,
    days: int = Query(30, ge=1, le=365, description="天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    獲取特定股票的預測歷史與準確度
    """
    return tracker.get_accuracy_statistics(
        db=db,
        days=days,
        stock_id=stock_id
    )


@router.get("/stock/{stock_id}/timeline")
def get_stock_prediction_timeline(
    stock_id: str,
    days: int = Query(90, ge=1, le=365, description="回溯天數"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    獲取特定股票的預測時間軸（用於疊加在 K 線上）

    回傳該股票歷史所有預測點，每個點包含：
    - 預測方向（UP/DOWN）
    - 預測日期 vs 目標日期
    - 命中與否
    - 預測誤差

    可直接給前端 K 線圖用來繪製命中/未中標記。
    """
    # 自動更新尚未驗證的預測結果
    try:
        tracker.update_actual_results(db=db)
    except Exception as e:
        logger.warning(f"Auto-update prediction results failed: {e}")

    return tracker.get_stock_timeline(db=db, stock_id=stock_id, days=days)


@router.get("/all-stocks")
def get_all_stocks_statistics(
    days: int = Query(30, ge=1, le=365, description="統計天數"),
    market: Optional[str] = Query(None, description="市場過濾: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    獲取所有股票的預測統計（依股票分組）

    Returns:
        - total_stocks: 有預測的股票數
        - total_predictions: 總預測數
        - overall_accuracy: 整體方向準確率
        - overall_avg_error: 整體平均誤差
        - stocks: 各股票詳細統計
    """
    # 自動更新尚未驗證的預測結果
    try:
        tracker.update_actual_results(db=db, market=market)
    except Exception as e:
        logger.warning(f"Auto-update prediction results failed: {e}")

    return tracker.get_all_stocks_statistics(db=db, days=days, market=market)


@router.get("/today")
def get_today_predictions(
    market: Optional[str] = Query(None, description="市場過濾: TW or US"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    獲取今日預測結果：
    1. 目標日期為今天的預測（已到期，可驗證）
    2. 今天產生的預測（pending，尚未到期）
    """
    # 自動更新尚未驗證的預測結果
    try:
        tracker.update_actual_results(db=db, market=market)
    except Exception as e:
        logger.warning(f"Auto-update prediction results failed: {e}")

    # 目標日期為今天的（可驗證的）
    target_today = tracker.get_daily_summary(db=db, target_date=date.today(), market=market)

    # 今天產生的預測（包含尚未到期的）
    made_today = tracker.get_predictions_made_on(db=db, prediction_date=date.today(), market=market)

    return {
        **target_today,
        "made_today": made_today,
    }
