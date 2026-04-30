"""
日曆 API
GET /api/calendar/earnings - 財報日曆
GET /api/calendar/dividends - 除息日曆
GET /api/calendar/economic - 經濟行事曆
GET /api/calendar/trading-status - 交易日狀態（含國定假日）
"""
from fastapi import APIRouter, Query
from datetime import date

from app.services.calendar_service import CalendarService
from app.services.trading_calendar import (
    is_trading_day,
    get_next_trading_date,
    get_previous_trading_date,
    get_calendar_gap_days,
)

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])

_service = CalendarService()


@router.get("/trading-status")
def get_trading_status(
    market: str = Query("TW", description="市場: TW 或 US"),
):
    """
    取得指定市場「今日」的交易狀態，供前端顯示「休市/開盤中/已收盤」。

    Returns:
        - market: 市場代碼
        - today: 今日日期 (YYYY-MM-DD)
        - is_trading_day: 今日是否為交易日（排除週末與國定假日）
        - next_trading_date: 下一個交易日
        - previous_trading_date: 上一個交易日
        - gap_days: 上一個交易日到下一個交易日的日曆天數差
        - long_gap: gap_days >= 4，代表長假後開盤
    """
    today = date.today()
    market = market.upper() if market else "TW"
    is_open = is_trading_day(today, market=market)
    next_d = get_next_trading_date(today, market=market)
    prev_d = get_previous_trading_date(today, market=market)
    gap = get_calendar_gap_days(today, market=market)
    return {
        "market": market,
        "today": today.isoformat(),
        "is_trading_day": is_open,
        "next_trading_date": next_d.isoformat(),
        "previous_trading_date": prev_d.isoformat(),
        "gap_days": gap,
        "long_gap": gap >= 4,
    }


@router.get("/earnings")
def get_earnings_calendar(
    market: str = Query("TW", description="市場: TW 或 US"),
    month: int = Query(None, ge=1, le=12, description="月份"),
    year: int = Query(None, description="年份"),
):
    """取得財報公佈日曆"""
    return _service.get_earnings_calendar(market=market, month=month, year=year)


@router.get("/dividends")
def get_dividend_calendar(
    market: str = Query("TW", description="市場: TW 或 US"),
    month: int = Query(None, ge=1, le=12, description="月份"),
    year: int = Query(None, description="年份"),
):
    """取得除權息日曆"""
    return _service.get_dividend_calendar(market=market, month=month, year=year)


@router.get("/economic")
def get_economic_calendar(
    market: str = Query("TW", description="市場: TW 或 US"),
    month: int = Query(None, ge=1, le=12, description="月份"),
    year: int = Query(None, description="年份"),
):
    """取得經濟行事曆（CPI、GDP、FOMC、非農等）"""
    return _service.get_economic_calendar(market=market, month=month, year=year)
