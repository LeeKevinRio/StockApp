"""
策略回測 API Router
"""
import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.stock_data_service import StockDataService
from app.services.strategy_backtest_engine import StrategyBacktestEngine, STRATEGIES
from app.schemas.strategy_backtest import (
    BacktestRequest,
    BacktestResult,
    StrategyListResponse,
    StrategyInfo,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/strategy-backtest", tags=["Strategy Backtest"])

_engine = StrategyBacktestEngine()
_stock_service = StockDataService()


@router.get("/strategies", response_model=StrategyListResponse)
def list_strategies():
    """列出所有可用策略及其參數說明"""
    items = [
        StrategyInfo(
            name=s["name"],
            display_name=s["display_name"],
            description=s["description"],
            default_params=s["default_params"],
        )
        for s in STRATEGIES.values()
    ]
    return StrategyListResponse(strategies=items)


@router.post("/run", response_model=BacktestResult)
def run_backtest(req: BacktestRequest, db: Session = Depends(get_db)):
    """執行策略回測"""
    # 驗證策略
    if req.strategy not in STRATEGIES:
        raise HTTPException(400, f"不支援的策略: {req.strategy}")

    # 驗證日期
    try:
        start = datetime.strptime(req.start_date, "%Y-%m-%d")
        end = datetime.strptime(req.end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(400, "日期格式錯誤，請使用 YYYY-MM-DD")

    if start >= end:
        raise HTTPException(400, "起始日期必須早於結束日期")

    # 計算需要的天數
    days_needed = (end - start).days + 60  # 多抓 60 天供指標暖機

    try:
        # 取得歷史資料
        history = _stock_service.get_history(
            db, req.stock_id, days=days_needed, market=req.market
        )

        if not history:
            raise HTTPException(404, f"找不到 {req.stock_id} 的歷史資料")

        # 過濾日期範圍（保留暖機期資料供指標計算）
        # 先用全部資料跑回測，之後只回傳範圍內的結果
        filtered = [
            h for h in history
            if req.start_date <= h["date"] <= req.end_date
        ]

        if len(filtered) < 10:
            raise HTTPException(400, "日期範圍內歷史資料不足（至少需要 10 筆）")

        # 用全部資料（含暖機期）跑回測
        result = _engine.run_backtest(
            history=history,
            strategy=req.strategy,
            params=req.params,
            initial_capital=req.initial_capital,
        )

        # 過濾結果只保留日期範圍內
        result["equity_curve"] = [
            p for p in result["equity_curve"]
            if req.start_date <= p["date"] <= req.end_date
        ]
        result["signals"] = [
            s for s in result["signals"]
            if req.start_date <= s["date"] <= req.end_date
        ]
        result["trades"] = [
            t for t in result["trades"]
            if req.start_date <= t["entry_date"] <= req.end_date
        ]

        # 取得股票名稱
        stock_name = ""
        try:
            stock_info = _stock_service.get_stock(db, req.stock_id, market=req.market)
            if stock_info:
                stock_name = stock_info.get("name", "")
        except Exception:
            pass

        return BacktestResult(
            stock_id=req.stock_id,
            stock_name=stock_name,
            strategy=result["strategy"],
            params=result["params"],
            metrics=result["metrics"],
            equity_curve=result["equity_curve"],
            trades=result["trades"],
            signals=result["signals"],
        )

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        logger.error(f"回測執行失敗: {e}", exc_info=True)
        raise HTTPException(500, f"回測執行失敗: {str(e)}")
