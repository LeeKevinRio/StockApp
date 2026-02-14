"""
宏觀經濟數據抓取器
使用 yfinance 抓取 VIX、美元指數、美股期貨等宏觀數據
計算綜合 macro_score (-100 ~ +100)
"""
import yfinance as yf
import time
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MacroDataFetcher:
    """宏觀經濟數據抓取器"""

    # 宏觀指標代碼
    SYMBOLS = {
        "vix": "^VIX",           # VIX 恐慌指數
        "dxy": "DX-Y.NYB",      # 美元指數
        "sp500_future": "ES=F",  # S&P 500 期貨
        "nasdaq_future": "NQ=F", # 納斯達克期貨
        "us10y": "^TNX",         # 美國 10 年期公債殖利率
        "gold": "GC=F",         # 黃金期貨
    }

    def __init__(self):
        self.last_request_time = 0
        self.request_interval = 0.3
        self._cache = {}
        self._cache_ttl = 1800  # 快取 30 分鐘

    def _rate_limit(self):
        """簡易限速"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _fetch_symbol_data(self, symbol: str, period: str = "5d") -> Optional[Dict]:
        """抓取單一指標的數據"""
        cache_key = f"macro_{symbol}_{period}"
        now = time.time()

        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data

        self._rate_limit()

        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period)

            if hist.empty or len(hist) < 2:
                return None

            latest = hist.iloc[-1]
            prev = hist.iloc[-2]
            first = hist.iloc[0]

            result = {
                "symbol": symbol,
                "latest_close": round(float(latest["Close"]), 4),
                "prev_close": round(float(prev["Close"]), 4),
                "first_close": round(float(first["Close"]), 4),
                "daily_change": round(float(latest["Close"] - prev["Close"]), 4),
                "daily_change_pct": round(
                    (float(latest["Close"]) - float(prev["Close"])) / float(prev["Close"]) * 100, 2
                ),
                "period_change_pct": round(
                    (float(latest["Close"]) - float(first["Close"])) / float(first["Close"]) * 100, 2
                ),
            }

            self._cache[cache_key] = (result, now)
            return result

        except Exception as e:
            logger.error(f"抓取 {symbol} 數據失敗: {e}")
            return None

    def fetch_all_macro_data(self) -> Dict:
        """抓取所有宏觀數據"""
        result = {}

        for name, symbol in self.SYMBOLS.items():
            data = self._fetch_symbol_data(symbol)
            if data:
                result[name] = data
            else:
                result[name] = {"symbol": symbol, "error": "數據不可用"}

        return result

    def calculate_macro_score(self, macro_data: Optional[Dict] = None) -> Dict:
        """
        計算宏觀面綜合評分 (-100 ~ +100)

        評分邏輯：
        - VIX 低 = 市場樂觀 → 加分；VIX 高 = 市場恐慌 → 減分
        - 美元指數走強 → 對新興市場/台股減分
        - 美股期貨上漲 → 加分
        - 10 年公債殖利率急升 → 減分（壓縮估值）
        - 黃金大漲 → 避險情緒增，減分
        """
        if macro_data is None:
            macro_data = self.fetch_all_macro_data()

        score = 0
        details = {}

        # === VIX 恐慌指數（權重 30%）===
        vix = macro_data.get("vix", {})
        vix_value = vix.get("latest_close", 20)
        if not isinstance(vix_value, (int, float)):
            vix_value = 20

        if vix_value < 12:
            vix_score = 30      # 極度樂觀
        elif vix_value < 16:
            vix_score = 20      # 樂觀
        elif vix_value < 20:
            vix_score = 10      # 正常偏樂觀
        elif vix_value < 25:
            vix_score = -5      # 輕微不安
        elif vix_value < 30:
            vix_score = -15     # 恐慌
        elif vix_value < 35:
            vix_score = -25     # 高度恐慌
        else:
            vix_score = -30     # 極度恐慌

        score += vix_score
        details["vix"] = {
            "value": vix_value,
            "score": vix_score,
            "signal": "極度恐慌" if vix_value >= 35 else "恐慌" if vix_value >= 25 else "正常" if vix_value >= 16 else "樂觀"
        }

        # === 美元指數（權重 15%）===
        dxy = macro_data.get("dxy", {})
        dxy_change = dxy.get("period_change_pct", 0)
        if not isinstance(dxy_change, (int, float)):
            dxy_change = 0

        # 美元走強對台股不利
        if dxy_change > 1.5:
            dxy_score = -15     # 美元急升，資金外流風險
        elif dxy_change > 0.5:
            dxy_score = -8
        elif dxy_change > -0.5:
            dxy_score = 0       # 美元穩定
        elif dxy_change > -1.5:
            dxy_score = 8       # 美元走弱，利於新興市場
        else:
            dxy_score = 15

        score += dxy_score
        details["dxy"] = {
            "value": dxy.get("latest_close", 0),
            "change_pct": dxy_change,
            "score": dxy_score,
            "signal": "美元走強_資金外流風險" if dxy_change > 0.5 else "美元走弱_利於新興市場" if dxy_change < -0.5 else "美元穩定"
        }

        # === 美股期貨（權重 30%）===
        sp_data = macro_data.get("sp500_future", {})
        nq_data = macro_data.get("nasdaq_future", {})
        sp_change = sp_data.get("daily_change_pct", 0)
        nq_change = nq_data.get("daily_change_pct", 0)
        if not isinstance(sp_change, (int, float)):
            sp_change = 0
        if not isinstance(nq_change, (int, float)):
            nq_change = 0

        avg_futures_change = (sp_change + nq_change) / 2

        if avg_futures_change > 1.5:
            futures_score = 30   # 期貨大漲
        elif avg_futures_change > 0.5:
            futures_score = 18
        elif avg_futures_change > 0:
            futures_score = 8
        elif avg_futures_change > -0.5:
            futures_score = -8
        elif avg_futures_change > -1.5:
            futures_score = -18
        else:
            futures_score = -30  # 期貨大跌

        score += futures_score
        details["us_futures"] = {
            "sp500_change_pct": sp_change,
            "nasdaq_change_pct": nq_change,
            "avg_change_pct": round(avg_futures_change, 2),
            "score": futures_score,
            "signal": "美股期貨大漲" if avg_futures_change > 1 else "美股期貨上漲" if avg_futures_change > 0 else "美股期貨下跌" if avg_futures_change > -1 else "美股期貨大跌"
        }

        # === 10 年公債殖利率（權重 15%）===
        us10y = macro_data.get("us10y", {})
        us10y_change = us10y.get("daily_change_pct", 0)
        us10y_value = us10y.get("latest_close", 4.0)
        if not isinstance(us10y_change, (int, float)):
            us10y_change = 0
        if not isinstance(us10y_value, (int, float)):
            us10y_value = 4.0

        # 殖利率急升壓縮成長股估值
        if us10y_change > 3:
            bond_score = -15    # 殖利率飆升
        elif us10y_change > 1:
            bond_score = -8
        elif us10y_change > -1:
            bond_score = 0
        elif us10y_change > -3:
            bond_score = 8
        else:
            bond_score = 15     # 殖利率大降

        score += bond_score
        details["us10y"] = {
            "value": us10y_value,
            "change_pct": us10y_change,
            "score": bond_score,
            "signal": "殖利率飆升_壓縮估值" if us10y_change > 1 else "殖利率下降_利於成長股" if us10y_change < -1 else "殖利率穩定"
        }

        # === 黃金（權重 10%）===
        gold = macro_data.get("gold", {})
        gold_change = gold.get("daily_change_pct", 0)
        if not isinstance(gold_change, (int, float)):
            gold_change = 0

        # 黃金大漲 = 避險情緒增加
        if gold_change > 2:
            gold_score = -10    # 強烈避險
        elif gold_change > 0.5:
            gold_score = -5
        elif gold_change > -0.5:
            gold_score = 0
        elif gold_change > -2:
            gold_score = 5
        else:
            gold_score = 10     # 風險偏好增加

        score += gold_score
        details["gold"] = {
            "value": gold.get("latest_close", 0),
            "change_pct": gold_change,
            "score": gold_score,
            "signal": "避險情緒升溫" if gold_change > 0.5 else "風險偏好增加" if gold_change < -0.5 else "黃金穩定"
        }

        # 限制總分在 -100 ~ +100
        score = max(-100, min(100, score))

        return {
            "macro_score": score,
            "macro_signal": (
                "strong_bullish_宏觀面強烈看多" if score >= 50 else
                "bullish_宏觀面看多" if score >= 20 else
                "neutral_宏觀面中性" if score >= -20 else
                "bearish_宏觀面看空" if score >= -50 else
                "strong_bearish_宏觀面強烈看空"
            ),
            "details": details,
            "raw_data": macro_data,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


    def calculate_combined_macro_score(self) -> Dict:
        """
        綜合宏觀評分：結合市場指標 + FRED 經濟數據
        市場指標權重 60%，FRED 經濟指標權重 40%
        """
        market_result = self.calculate_macro_score()
        market_score = market_result.get("macro_score", 0)

        # 嘗試取得 FRED 數據
        fred_score = 0
        fred_details = {}
        try:
            from app.data_fetchers.fred_fetcher import FREDFetcher
            from app.config import settings
            if settings.FRED_API_KEY:
                fred = FREDFetcher(api_key=settings.FRED_API_KEY)
                fred_result = fred.calculate_economic_score()
                fred_score = fred_result.get("economic_score", 0)
                fred_details = fred_result.get("details", {})
        except Exception as e:
            logger.warning(f"FRED 數據整合失敗: {e}")

        # 加權合併
        combined = int(market_score * 0.6 + fred_score * 0.4)
        combined = max(-100, min(100, combined))

        result = market_result.copy()
        result["macro_score"] = combined
        result["market_score_raw"] = market_score
        result["economic_score_raw"] = fred_score
        result["fred_details"] = fred_details
        result["macro_signal"] = (
            "strong_bullish_宏觀面強烈看多" if combined >= 50 else
            "bullish_宏觀面看多" if combined >= 20 else
            "neutral_宏觀面中性" if combined >= -20 else
            "bearish_宏觀面看空" if combined >= -50 else
            "strong_bearish_宏觀面強烈看空"
        )

        return result


# 全域實例
macro_data_fetcher = MacroDataFetcher()
