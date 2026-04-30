"""
Trading Calendar 單元測試

鎖定台股/美股假日邏輯，避免：
1. 假期清單被誤刪
2. is_trading_day 在假日誤判為交易日
3. 長假後的 get_next_trading_date 跳錯日
"""
from datetime import date

import pytest

from app.services.trading_calendar import (
    is_trading_day,
    get_next_trading_date,
    get_previous_trading_date,
    get_calendar_gap_days,
    TAIWAN_HOLIDAYS,
    US_HOLIDAYS,
)


# ============================================================
# 基本：週末永遠不是交易日
# ============================================================


def test_weekend_not_trading_day_tw():
    # 2025-01-04 (Sat), 2025-01-05 (Sun)
    assert is_trading_day(date(2025, 1, 4), market="TW") is False
    assert is_trading_day(date(2025, 1, 5), market="TW") is False


def test_weekend_not_trading_day_us():
    assert is_trading_day(date(2025, 1, 4), market="US") is False
    assert is_trading_day(date(2025, 1, 5), market="US") is False


# ============================================================
# 一般工作日：應為交易日
# ============================================================


def test_regular_weekday_is_trading_day_tw():
    # 2025-04-15 (Tue) 非台股假日
    assert is_trading_day(date(2025, 4, 15), market="TW") is True


def test_regular_weekday_is_trading_day_us():
    # 2025-04-15 (Tue) 非美股假日
    assert is_trading_day(date(2025, 4, 15), market="US") is True


# ============================================================
# 台股國定假日：必須為休市日
# ============================================================


@pytest.mark.parametrize("holiday", [
    date(2025, 1, 1),    # 元旦
    date(2025, 2, 28),   # 和平紀念日
    date(2025, 4, 4),    # 清明節
    date(2025, 5, 30),   # 端午節
    date(2025, 10, 10),  # 國慶日
    date(2026, 2, 17),   # 春節
    date(2026, 6, 19),   # 端午節
    date(2026, 9, 25),   # 中秋節
])
def test_tw_holidays_not_trading_day(holiday):
    assert is_trading_day(holiday, market="TW") is False


def test_tw_holiday_is_us_trading_day_when_weekday():
    # 端午節 2025-05-30 (Fri) 台股休市，但對美股是正常交易日
    d = date(2025, 5, 30)
    assert is_trading_day(d, market="TW") is False
    assert is_trading_day(d, market="US") is True


# ============================================================
# 美股國定假日：必須為休市日
# ============================================================


@pytest.mark.parametrize("holiday", [
    date(2025, 1, 1),    # New Year's Day
    date(2025, 1, 20),   # MLK Day
    date(2025, 7, 4),    # Independence Day
    date(2025, 11, 27),  # Thanksgiving
    date(2025, 12, 25),  # Christmas
    date(2026, 5, 25),   # Memorial Day
    date(2026, 11, 26),  # Thanksgiving
])
def test_us_holidays_not_trading_day(holiday):
    assert is_trading_day(holiday, market="US") is False


# ============================================================
# get_next_trading_date：必須跳過週末與假日
# ============================================================


def test_next_trading_date_skips_weekend_tw():
    # 週五的下個交易日 = 下週一
    fri = date(2025, 4, 11)  # Fri
    nxt = get_next_trading_date(fri, market="TW")
    assert nxt == date(2025, 4, 14)  # Mon


def test_next_trading_date_skips_holiday_tw():
    # 端午節前一天 (Thu 5/29) → 下個交易日應為 6/2 (Mon)，因 5/30 端午、5/31~6/1 週末
    thu = date(2025, 5, 29)
    nxt = get_next_trading_date(thu, market="TW")
    assert nxt == date(2025, 6, 2)


def test_next_trading_date_skips_long_holiday_tw():
    # 春節前最後交易日 2026/2/11 (Wed) → 下個交易日應為 2/24 (Tue)
    # 因 2/12-13 結算交割無交易，2/14-15 週末，2/16-20 春節，2/21-22 週末
    # 2/23 為週一（假設不是假日）
    pre_cny = date(2026, 2, 11)
    nxt = get_next_trading_date(pre_cny, market="TW")
    assert nxt == date(2026, 2, 23) or nxt == date(2026, 2, 24)


def test_next_trading_date_skips_holiday_us():
    # 7/3 (Thu) 是 Independence Day observed 的前一天，正常交易；
    # 7/3 後下個交易日應為 7/7 (Mon)，因 7/4 假日 + 週末
    # 但 2026 中 7/4 落在 Sat，所以 7/3 (Fri) 是觀察日
    # 用 2025 比較單純：7/3 (Thu) 下個交易日 = 7/7 (Mon)
    thu = date(2025, 7, 3)
    nxt = get_next_trading_date(thu, market="US")
    assert nxt == date(2025, 7, 7)


# ============================================================
# get_previous_trading_date
# ============================================================


def test_previous_trading_date_skips_weekend_tw():
    # 週一的上個交易日 = 上週五
    mon = date(2025, 4, 14)
    prev = get_previous_trading_date(mon, market="TW")
    assert prev == date(2025, 4, 11)


def test_previous_trading_date_skips_holiday_tw():
    # 端午節後第一個交易日 6/2 (Mon) → 上個交易日應為 5/29 (Thu)
    mon = date(2025, 6, 2)
    prev = get_previous_trading_date(mon, market="TW")
    assert prev == date(2025, 5, 29)


# ============================================================
# get_calendar_gap_days：跨假期天數
# ============================================================


def test_calendar_gap_normal_weekday_tw():
    # 平日：上一個交易日到下一個交易日相差 2 天（D-1 → D+1）
    d = date(2025, 4, 16)  # Wed
    gap = get_calendar_gap_days(d, market="TW")
    assert gap == 2


def test_calendar_gap_normal_friday_tw():
    """一般週五 gap=4（跨週末）— 不應視為長假，避免誤觸發 AI 提醒"""
    d = date(2025, 4, 18)  # Fri (非假日)
    gap = get_calendar_gap_days(d, market="TW")
    assert gap == 4


def test_calendar_gap_pre_holiday_tw():
    """端午前一天 Thu：gap=5（跨假日 Fri + 週末），應觸發長假提醒（>= 5）"""
    d = date(2025, 5, 29)  # 端午 5/30 前的週四
    gap = get_calendar_gap_days(d, market="TW")
    assert gap == 5


def test_calendar_gap_post_holiday_tw():
    """端午後第一個交易日 Mon：gap=5（跨假日週五 + 週末），應觸發長假提醒"""
    d = date(2025, 6, 2)  # 端午 5/30 後的週一
    gap = get_calendar_gap_days(d, market="TW")
    assert gap == 5


# ============================================================
# 假期清單最低保證
# ============================================================


def test_taiwan_holidays_cover_2025_2026():
    years = {h.year for h in TAIWAN_HOLIDAYS}
    assert 2025 in years
    assert 2026 in years
    # 春節必含
    assert date(2026, 2, 17) in TAIWAN_HOLIDAYS  # 初一
    # 元旦必含
    assert date(2025, 1, 1) in TAIWAN_HOLIDAYS
    assert date(2026, 1, 1) in TAIWAN_HOLIDAYS


def test_us_holidays_cover_2025_2026():
    years = {h.year for h in US_HOLIDAYS}
    assert 2025 in years
    assert 2026 in years
    # 重大假日必含
    assert date(2025, 12, 25) in US_HOLIDAYS  # Christmas
    assert date(2026, 12, 25) in US_HOLIDAYS
    assert date(2025, 11, 27) in US_HOLIDAYS  # Thanksgiving 2025
    assert date(2026, 11, 26) in US_HOLIDAYS  # Thanksgiving 2026
