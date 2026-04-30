"""
日曆 API
GET /api/calendar/earnings - 財報日曆
GET /api/calendar/dividends - 除息日曆
GET /api/calendar/economic - 經濟行事曆
GET /api/calendar/trading-status - 交易日狀態（含國定假日）
"""
from fastapi import APIRouter, Query
from datetime import date, timedelta

from app.services.calendar_service import CalendarService
from app.services.trading_calendar import (
    is_trading_day,
    get_next_trading_date,
    get_previous_trading_date,
    get_calendar_gap_days,
    TAIWAN_HOLIDAYS,
    US_HOLIDAYS,
)

router = APIRouter(prefix="/api/calendar", tags=["Calendar"])

_service = CalendarService()


@router.get("/holidays")
def get_market_holidays(
    market: str = Query("TW", description="市場: TW 或 US"),
    days: int = Query(90, ge=7, le=365, description="未來多少天內"),
):
    """
    取得未來 N 天內的市場休市日清單（含名稱）。

    用途：
    - 前端日曆/即時時鐘卡可在此先預覽接下來的長假
    - 讓使用者一眼看出下個交易日

    Returns:
        - market: 市場代碼
        - from_date / to_date: 查詢範圍
        - holidays: [{date, weekday, name}]，date 升序
    """
    market = market.upper() if market else "TW"
    src = US_HOLIDAYS if market == "US" else TAIWAN_HOLIDAYS

    today = date.today()
    end = today + timedelta(days=days)

    # 為了在 API 上提供「假日名稱」，這裡用一個小型查表
    # （與 trading_calendar 內的中文註解對應，缺項 fallback 為空字串）
    name_map_tw = {
        (1, 1): "元旦",
        (2, 28): "和平紀念日",
        (4, 4): "清明節",
        (4, 5): "兒童節 / 清明節",
        (5, 1): "勞動節",
        (10, 10): "國慶日",
        (12, 25): "行憲紀念日",
    }
    name_map_us = {
        (1, 1): "New Year's Day",
        (7, 4): "Independence Day",
        (12, 25): "Christmas Day",
        (6, 19): "Juneteenth",
    }
    name_map = name_map_us if market == "US" else name_map_tw

    weekday_tw = ["一", "二", "三", "四", "五", "六", "日"]
    holidays = []
    for d in sorted(src):
        if today <= d <= end:
            name = name_map.get((d.month, d.day), "市場休市")
            holidays.append({
                "date": d.isoformat(),
                "weekday": f"週{weekday_tw[d.weekday()]}" if market == "TW"
                else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][d.weekday()],
                "name": name,
            })

    return {
        "market": market,
        "from_date": today.isoformat(),
        "to_date": end.isoformat(),
        "total": len(holidays),
        "holidays": holidays,
    }


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
        - long_gap: gap_days >= 5，代表跨國定假日（避免一般 Fri→Mon 週末誤判）
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
        "long_gap": gap >= 5,
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
