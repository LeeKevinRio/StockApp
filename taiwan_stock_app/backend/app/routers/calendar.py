"""
日曆 API
GET /api/calendar/earnings - 財報日曆
GET /api/calendar/dividends - 除息日曆
GET /api/calendar/economic - 經濟行事曆
"""
from fastapi import APIRouter, Query
from datetime import date

from app.services.calendar_service import CalendarService

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])

_service = CalendarService()


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
