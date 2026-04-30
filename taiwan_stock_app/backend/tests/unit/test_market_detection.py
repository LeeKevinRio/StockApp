"""
prediction_tracker._detect_market 單元測試

鎖定市場偵測邏輯：
- 純英文 → 美股 (AAPL, MSFT, NVDA)
- 純數字 / 數字開頭含字母（ETF 如 00631L） → 台股
- 其他特殊代碼 → 退回 market_hint
這個 heuristic 在 portfolio_service / trading_service / portfolio_recommendation_service
都被沿用，必須穩固。
"""
import pytest

from app.services.prediction_tracker import PredictionTracker


@pytest.mark.parametrize("stock_id", [
    "AAPL", "MSFT", "NVDA", "TSLA", "GOOGL", "GOOG", "AMZN", "META",
])
def test_us_pure_alpha(stock_id):
    assert PredictionTracker._detect_market(stock_id) == "US"


@pytest.mark.parametrize("stock_id", [
    "2330",   # 台積電
    "2317",   # 鴻海
    "2454",   # 聯發科
    "0050",   # 元大台灣 50
    "00631L", # 台灣 50 正 2（ETF，數字+字母）
    "1101",   # 台泥
])
def test_tw_starts_with_digit(stock_id):
    assert PredictionTracker._detect_market(stock_id) == "TW"


def test_market_hint_used_when_neither():
    # 帶 . 的代碼（罕見），不確定時用 hint
    assert PredictionTracker._detect_market(".AAPL", market_hint="US") == "US"
    assert PredictionTracker._detect_market(".AAPL", market_hint="TW") == "TW"


def test_us_with_dot_suffix_falls_through_to_hint():
    """BRK.B 不是純 isalpha（含 .），也不是 digit 開頭 → 退回 hint"""
    # 此函式設計上把 BRK.B 視為「不確定」，會回 hint。實務上 BRK.B
    # 應由 caller 顯式傳 market="US"。
    assert PredictionTracker._detect_market("BRK.B", market_hint="US") == "US"


def test_default_hint_is_tw():
    """無 hint 時預設台股"""
    assert PredictionTracker._detect_market("BRK.B") == "TW"
