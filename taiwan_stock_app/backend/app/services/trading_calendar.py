"""
股市交易日曆工具（支援台股 TW 與美股 US）

提供台股/美股休市日判斷、下一個/上一個交易日計算功能。
- 台股休市日來源：台灣證券交易所公告
- 美股休市日來源：NYSE/NASDAQ 固定假日
"""
from datetime import date, timedelta
from typing import Set

# ============================================================
# 台灣股市休市日（2025-2027）
# 來源：台灣證券交易所每年公告之「封關日/開紅盤日」與休市日曆
# ============================================================

TAIWAN_HOLIDAYS: Set[date] = {
    # ========== 2025 年（來源：經理人/TWSE 確認）==========
    date(2025, 1, 1),   # 元旦
    # 春節：封關日 1/22，1/23-24 結算交割無交易，1/27-31 春節假期
    date(2025, 1, 23),  # 結算交割（無交易）
    date(2025, 1, 24),  # 結算交割（無交易）
    date(2025, 1, 27),  # 調整放假
    date(2025, 1, 28),  # 農曆春節
    date(2025, 1, 29),  # 農曆春節
    date(2025, 1, 30),  # 農曆春節
    date(2025, 1, 31),  # 農曆春節
    date(2025, 2, 28),  # 和平紀念日
    date(2025, 4, 3),   # 兒童節
    date(2025, 4, 4),   # 清明節
    date(2025, 5, 1),   # 勞動節
    date(2025, 5, 30),  # 端午節
    date(2025, 10, 6),  # 中秋節
    date(2025, 10, 10), # 國慶日

    # ========== 2026 年（來源：TWSE 證交所 API 確認）==========
    date(2026, 1, 1),   # 元旦
    # 春節：封關日 2/11，2/12-13 結算交割無交易，2/16-20 春節假期
    date(2026, 2, 12),  # 結算交割（無交易）
    date(2026, 2, 13),  # 結算交割（無交易）
    date(2026, 2, 16),  # 除夕
    date(2026, 2, 17),  # 初一
    date(2026, 2, 18),  # 初二
    date(2026, 2, 19),  # 初三
    date(2026, 2, 20),  # 春節假期
    date(2026, 2, 27),  # 和平紀念日補假
    date(2026, 4, 3),   # 兒童節補假
    date(2026, 4, 6),   # 清明節補假
    date(2026, 5, 1),   # 勞動節
    date(2026, 6, 19),  # 端午節
    date(2026, 9, 25),  # 中秋節
    date(2026, 9, 28),  # 教師節
    date(2026, 10, 9),  # 國慶日補假
    date(2026, 10, 26), # 臺灣光復節補假
    date(2026, 12, 25), # 行憲紀念日

    # ========== 2027 年（預估，TWSE 尚未公告，届時需更新）==========
    date(2027, 1, 1),   # 元旦
    # 春節：除夕 2/5（五），初一 2/6（六）
    date(2027, 2, 4),   # 結算交割（預估）
    date(2027, 2, 5),   # 除夕
    date(2027, 2, 8),   # 初三
    date(2027, 2, 9),   # 初四
    date(2027, 2, 10),  # 春節假期
    date(2027, 3, 1),   # 和平紀念日補假（2/28 為週日）
    date(2027, 4, 5),   # 兒童節 / 清明節
    date(2027, 6, 9),   # 端午節
    date(2027, 9, 15),  # 中秋節
    date(2027, 9, 28),  # 教師節（預估）
    date(2027, 10, 11), # 國慶日補假（10/10 為週日）
    date(2027, 10, 25), # 臺灣光復節（預估）
}


# ============================================================
# 美國股市休市日（2025-2027）
# 來源：NYSE/NASDAQ 官方假日行事曆
# 固定假日：New Year's, MLK Day, Presidents' Day, Good Friday,
#           Memorial Day, Juneteenth, Independence Day, Labor Day,
#           Thanksgiving, Christmas
# ============================================================

US_HOLIDAYS: Set[date] = {
    # ========== 2025 年 ==========
    date(2025, 1, 1),   # New Year's Day
    date(2025, 1, 20),  # Martin Luther King Jr. Day
    date(2025, 2, 17),  # Presidents' Day
    date(2025, 4, 18),  # Good Friday
    date(2025, 5, 26),  # Memorial Day
    date(2025, 6, 19),  # Juneteenth
    date(2025, 7, 4),   # Independence Day
    date(2025, 9, 1),   # Labor Day
    date(2025, 11, 27), # Thanksgiving Day
    date(2025, 12, 25), # Christmas Day

    # ========== 2026 年 ==========
    date(2026, 1, 1),   # New Year's Day
    date(2026, 1, 19),  # Martin Luther King Jr. Day
    date(2026, 2, 16),  # Presidents' Day
    date(2026, 4, 3),   # Good Friday
    date(2026, 5, 25),  # Memorial Day
    date(2026, 6, 19),  # Juneteenth
    date(2026, 7, 3),   # Independence Day (observed, 7/4 is Saturday)
    date(2026, 9, 7),   # Labor Day
    date(2026, 11, 26), # Thanksgiving Day
    date(2026, 12, 25), # Christmas Day

    # ========== 2027 年 ==========
    date(2027, 1, 1),   # New Year's Day
    date(2027, 1, 18),  # Martin Luther King Jr. Day
    date(2027, 2, 15),  # Presidents' Day
    date(2027, 3, 26),  # Good Friday
    date(2027, 5, 31),  # Memorial Day
    date(2027, 6, 18),  # Juneteenth (observed, 6/19 is Saturday)
    date(2027, 7, 5),   # Independence Day (observed, 7/4 is Sunday)
    date(2027, 9, 6),   # Labor Day
    date(2027, 11, 25), # Thanksgiving Day
    date(2027, 12, 24), # Christmas Day (observed, 12/25 is Saturday)
}


def _get_holidays(market: str = "TW") -> Set[date]:
    """取得指定市場的休市日集合"""
    if market == "US":
        return US_HOLIDAYS
    return TAIWAN_HOLIDAYS


def is_trading_day(d: date, market: str = "TW") -> bool:
    """
    判斷指定日期是否為交易日。

    Args:
        d: 要判斷的日期
        market: 市場 "TW"(台股) 或 "US"(美股)

    非交易日包含：週六、週日、該市場國定假日。
    """
    if d.weekday() >= 5:  # 週六(5) 或 週日(6)
        return False
    if d in _get_holidays(market):
        return False
    return True


def get_next_trading_date(from_date: date = None, market: str = "TW") -> date:
    """
    取得下一個交易日（不含 from_date 當天）。

    Args:
        from_date: 起算日期，預設為今天。
        market: 市場 "TW"(台股) 或 "US"(美股)

    Returns:
        下一個交易日的 date 物件。
    """
    if from_date is None:
        from_date = date.today()

    d = from_date + timedelta(days=1)
    while not is_trading_day(d, market):
        d += timedelta(days=1)
    return d


def get_previous_trading_date(from_date: date = None, market: str = "TW") -> date:
    """
    取得上一個交易日（不含 from_date 當天）。

    Args:
        from_date: 起算日期，預設為今天。
        market: 市場 "TW"(台股) 或 "US"(美股)

    Returns:
        上一個交易日的 date 物件。
    """
    if from_date is None:
        from_date = date.today()

    d = from_date - timedelta(days=1)
    while not is_trading_day(d, market):
        d -= timedelta(days=1)
    return d


def get_calendar_gap_days(from_date: date = None, market: str = "TW") -> int:
    """
    計算上一個交易日到下一個交易日之間的日曆天數差。

    正常工作日 → 1 天
    週末後開盤 → 3 天
    長假後開盤 → 7-10+ 天（春節等）

    Args:
        from_date: 基準日期，預設為今天
        market: 市場 "TW" 或 "US"

    Returns:
        日曆天數差
    """
    if from_date is None:
        from_date = date.today()

    prev = get_previous_trading_date(from_date, market)
    next_td = get_next_trading_date(from_date, market)
    return (next_td - prev).days
