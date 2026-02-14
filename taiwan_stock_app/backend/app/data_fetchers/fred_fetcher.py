"""
FRED (Federal Reserve Economic Data) 數據抓取器
抓取宏觀經濟指標：CPI、GDP、失業率、Fed 利率、10年公債殖利率
"""
import logging
import time
from typing import Dict, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class FREDFetcher:
    """FRED 宏觀經濟數據抓取器"""

    BASE_URL = "https://api.stlouisfed.org/fred"

    # 核心經濟指標
    INDICATORS = {
        "cpi": {
            "series_id": "CPIAUCSL",
            "name": "消費者物價指數 (CPI)",
            "frequency": "monthly",
        },
        "gdp": {
            "series_id": "GDP",
            "name": "美國 GDP",
            "frequency": "quarterly",
        },
        "unemployment": {
            "series_id": "UNRATE",
            "name": "失業率",
            "frequency": "monthly",
        },
        "fed_rate": {
            "series_id": "FEDFUNDS",
            "name": "聯邦基金利率",
            "frequency": "monthly",
        },
        "us10y_yield": {
            "series_id": "DGS10",
            "name": "10年期公債殖利率",
            "frequency": "daily",
        },
        "us2y_yield": {
            "series_id": "DGS2",
            "name": "2年期公債殖利率",
            "frequency": "daily",
        },
        "m2": {
            "series_id": "M2SL",
            "name": "M2 貨幣供給",
            "frequency": "monthly",
        },
    }

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._cache = {}
        self._cache_ttl = 3600  # 快取 1 小時
        self.last_request_time = 0
        self.request_interval = 0.5

    def _rate_limit(self):
        """簡易限速"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.request_interval:
            time.sleep(self.request_interval - elapsed)
        self.last_request_time = time.time()

    def _fetch_series(self, series_id: str, limit: int = 12) -> Optional[List[Dict]]:
        """從 FRED API 抓取時間序列數據"""
        if not self.api_key:
            logger.warning("FRED API Key 未設定，使用備用數據")
            return None

        cache_key = f"fred_{series_id}_{limit}"
        now = time.time()
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data

        self._rate_limit()

        try:
            import requests
            url = f"{self.BASE_URL}/series/observations"
            params = {
                "series_id": series_id,
                "api_key": self.api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": limit,
            }

            response = requests.get(url, params=params, timeout=15)
            if response.status_code != 200:
                logger.error(f"FRED API 回應錯誤: {response.status_code}")
                return None

            data = response.json()
            observations = data.get("observations", [])

            result = []
            for obs in observations:
                value = obs.get("value", ".")
                if value == ".":
                    continue
                result.append({
                    "date": obs["date"],
                    "value": float(value),
                })

            self._cache[cache_key] = (result, now)
            return result

        except Exception as e:
            logger.error(f"FRED API 抓取 {series_id} 失敗: {e}")
            return None

    def fetch_all_indicators(self) -> Dict:
        """抓取所有經濟指標"""
        result = {}

        for key, info in self.INDICATORS.items():
            data = self._fetch_series(info["series_id"])
            if data and len(data) >= 2:
                latest = data[0]
                prev = data[1]
                change = latest["value"] - prev["value"]
                change_pct = (change / prev["value"] * 100) if prev["value"] != 0 else 0

                result[key] = {
                    "name": info["name"],
                    "series_id": info["series_id"],
                    "latest_value": latest["value"],
                    "latest_date": latest["date"],
                    "prev_value": prev["value"],
                    "change": round(change, 4),
                    "change_pct": round(change_pct, 2),
                    "frequency": info["frequency"],
                }
            else:
                result[key] = {
                    "name": info["name"],
                    "series_id": info["series_id"],
                    "error": "數據不可用",
                }

        return result

    def calculate_economic_score(self, indicators: Optional[Dict] = None) -> Dict:
        """
        計算經濟環境評分 (-100 ~ +100)

        評分邏輯：
        - CPI 上升快 → 通膨壓力 → 減分
        - 失業率上升 → 經濟衰退風險 → 減分
        - Fed 利率高 → 緊縮 → 減分
        - 殖利率曲線倒掛 → 衰退訊號 → 大減分
        """
        if indicators is None:
            indicators = self.fetch_all_indicators()

        score = 0
        details = {}

        # === CPI 通膨（權重 25%）===
        cpi_data = indicators.get("cpi", {})
        cpi_change = cpi_data.get("change_pct", 0)
        if isinstance(cpi_change, (int, float)):
            if cpi_change > 0.5:
                cpi_score = -25     # 通膨加速
            elif cpi_change > 0.2:
                cpi_score = -12
            elif cpi_change > 0:
                cpi_score = -5      # 溫和通膨
            elif cpi_change > -0.2:
                cpi_score = 5       # 通膨趨緩
            else:
                cpi_score = 15      # 通膨明顯下降
        else:
            cpi_score = 0

        score += cpi_score
        details["cpi"] = {
            "value": cpi_data.get("latest_value"),
            "change_pct": cpi_change,
            "score": cpi_score,
            "signal": "通膨加速" if cpi_change > 0.3 else "通膨趨緩" if cpi_change < 0 else "通膨穩定"
        }

        # === 失業率（權重 20%）===
        unemp_data = indicators.get("unemployment", {})
        unemp_value = unemp_data.get("latest_value", 4.0)
        unemp_change = unemp_data.get("change", 0)
        if isinstance(unemp_value, (int, float)):
            if unemp_value < 3.5:
                unemp_score = 15    # 充分就業
            elif unemp_value < 4.5:
                unemp_score = 8     # 健康就業
            elif unemp_value < 5.5:
                unemp_score = -5
            elif unemp_value < 7:
                unemp_score = -15
            else:
                unemp_score = -20   # 高失業率

            # 趨勢修正
            if isinstance(unemp_change, (int, float)):
                if unemp_change > 0.3:
                    unemp_score -= 5    # 失業率上升
                elif unemp_change < -0.2:
                    unemp_score += 5    # 失業率下降
        else:
            unemp_score = 0

        score += unemp_score
        details["unemployment"] = {
            "value": unemp_value,
            "change": unemp_change,
            "score": unemp_score,
            "signal": "充分就業" if unemp_value < 4 else "就業健康" if unemp_value < 5 else "失業率偏高"
        }

        # === Fed 利率（權重 25%）===
        fed_data = indicators.get("fed_rate", {})
        fed_rate = fed_data.get("latest_value", 5.0)
        fed_change = fed_data.get("change", 0)
        if isinstance(fed_rate, (int, float)):
            if fed_rate > 5.5:
                fed_score = -20     # 緊縮
            elif fed_rate > 4.5:
                fed_score = -10
            elif fed_rate > 3:
                fed_score = 0       # 中性
            elif fed_rate > 1.5:
                fed_score = 10      # 寬鬆
            else:
                fed_score = 20      # 極度寬鬆

            # 趨勢修正
            if isinstance(fed_change, (int, float)):
                if fed_change > 0:
                    fed_score -= 5  # 升息
                elif fed_change < 0:
                    fed_score += 5  # 降息
        else:
            fed_score = 0

        score += fed_score
        details["fed_rate"] = {
            "value": fed_rate,
            "change": fed_change,
            "score": fed_score,
            "signal": "升息中" if fed_change > 0 else "降息中" if fed_change < 0 else "利率持平",
        }

        # === 殖利率曲線（權重 30%）===
        us10y = indicators.get("us10y_yield", {})
        us2y = indicators.get("us2y_yield", {})
        us10y_val = us10y.get("latest_value")
        us2y_val = us2y.get("latest_value")

        if isinstance(us10y_val, (int, float)) and isinstance(us2y_val, (int, float)):
            spread = us10y_val - us2y_val

            if spread < -0.5:
                yield_score = -30   # 嚴重倒掛，衰退警報
            elif spread < 0:
                yield_score = -15   # 倒掛
            elif spread < 0.5:
                yield_score = 0     # 扁平
            elif spread < 1.5:
                yield_score = 15    # 正常
            else:
                yield_score = 25    # 陡峭，經濟擴張

            details["yield_curve"] = {
                "us10y": us10y_val,
                "us2y": us2y_val,
                "spread": round(spread, 4),
                "score": yield_score,
                "signal": "殖利率嚴重倒掛_衰退風險" if spread < -0.5 else "殖利率倒掛" if spread < 0 else "殖利率正常" if spread < 1.5 else "殖利率陡峭_經濟擴張"
            }
        else:
            yield_score = 0
            details["yield_curve"] = {"error": "數據不可用", "score": 0}

        score += yield_score

        score = max(-100, min(100, score))

        return {
            "economic_score": score,
            "economic_signal": (
                "strong_positive_經濟環境非常有利" if score >= 40 else
                "positive_經濟環境有利" if score >= 15 else
                "neutral_經濟環境中性" if score >= -15 else
                "negative_經濟環境不利" if score >= -40 else
                "strong_negative_經濟環境非常不利"
            ),
            "details": details,
            "raw_data": indicators,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


# 全域實例
fred_fetcher = FREDFetcher()
