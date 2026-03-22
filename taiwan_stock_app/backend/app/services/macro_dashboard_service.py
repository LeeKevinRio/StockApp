"""
宏觀經濟儀表板服務
整合多個資料來源，提供全面的宏觀經濟分析與市場制度偵測
資料來源：FRED API、台灣經濟指標、全球資產價格
"""
import logging
import time
import asyncio
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import aiohttp

from app.data_fetchers.fred_fetcher import FREDFetcher

logger = logging.getLogger(__name__)


@dataclass
class EconomicHealthScore:
    """經濟健康評分"""
    us_score: float  # -100 ~ +100
    taiwan_score: float  # -100 ~ +100
    global_risk_score: float  # -100 ~ +100（負數表示高風險）
    yield_curve_status: str  # normal/flat/inverted
    inflation_trend: str  # rising/stable/falling


@dataclass
class MarketRegime:
    """市場制度"""
    regime: str  # risk_on / risk_off / transitioning
    vix_level: str  # low/medium/high
    yield_curve_signal: str  # normal/flat/inverted
    fed_direction: str  # hiking/cutting/neutral
    confidence: float  # 0-1


@dataclass
class SectorImpact:
    """扇區衝擊分析"""
    sector: str
    impact: str  # positive/neutral/negative
    score: float  # -100 ~ +100
    rationale: str


class MacroDashboardService:
    """宏觀經濟儀表板服務"""

    def __init__(self, fred_api_key: str = "", cache_ttl: int = 1800):
        """
        初始化服務

        Args:
            fred_api_key: FRED API 密鑰
            cache_ttl: 快取有效期（秒），預設 30 分鐘
        """
        self.fred_fetcher = FREDFetcher(api_key=fred_api_key)
        self.cache_ttl = cache_ttl
        self._cache = {}
        self._cache_time = {}

        # 歷史數據用於百分位計算（簡化版，實際應從數據庫取得）
        self._historical_benchmarks = {
            "cpi_change_pct": {"mean": 0.25, "std": 0.35, "min": -0.5, "max": 1.2},
            "unemployment": {"mean": 4.5, "std": 1.2, "min": 2.5, "max": 10.0},
            "fed_rate": {"mean": 3.5, "std": 2.0, "min": 0.0, "max": 6.5},
            "us10y_yield": {"mean": 3.0, "std": 1.5, "min": 1.0, "max": 7.0},
            "vix": {"mean": 18.0, "std": 8.0, "min": 9.0, "max": 80.0},
            "dxy": {"mean": 100.0, "std": 5.0, "min": 80.0, "max": 115.0},
        }

    def _is_cache_valid(self, key: str) -> bool:
        """檢查快取是否仍有效"""
        if key not in self._cache_time:
            return False
        elapsed = time.time() - self._cache_time[key]
        return elapsed < self.cache_ttl

    def _get_cached(self, key: str):
        """取得快取數據"""
        if self._is_cache_valid(key):
            return self._cache.get(key)
        return None

    def _set_cache(self, key: str, value):
        """設定快取數據"""
        self._cache[key] = value
        self._cache_time[key] = time.time()

    async def _fetch_external_data(self, url: str, timeout: int = 15) -> Optional[Dict]:
        """
        從外部 API 抓取數據

        Args:
            url: API URL
            timeout: 超時時間（秒）

        Returns:
            JSON 回應或 None
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.warning(f"外部 API 錯誤 {url}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"抓取外部數據失敗 {url}: {e}")
            return None

    def _get_vix_mock_data(self) -> float:
        """
        取得 VIX 模擬數據
        實際應從 Yahoo Finance 或 CBOE 取得
        """
        # 模擬數據，實際應連接真實 API
        return 16.5

    def _get_dxy_mock_data(self) -> float:
        """
        取得美元指數 (DXY) 模擬數據
        實際應從 TradingView 或其他來源取得
        """
        return 104.2

    def _get_gold_price_mock_data(self) -> float:
        """取得黃金價格模擬數據"""
        return 2150.0

    def _get_oil_wti_mock_data(self) -> float:
        """取得 WTI 原油價格模擬數據"""
        return 78.5

    def _get_taiex_mock_data(self) -> Tuple[float, float]:
        """
        取得加權指數模擬數據
        Returns: (current_price, change_pct)
        """
        return (21500.0, 0.5)

    def _get_twd_usd_rate_mock_data(self) -> float:
        """取得 TWD/USD 匯率模擬數據"""
        return 32.1

    def _get_taiwan_cpi_mock_data(self) -> Tuple[float, float]:
        """
        取得台灣 CPI 模擬數據
        Returns: (cpi_value, change_pct)
        """
        return (110.5, 0.18)

    def calculate_economic_health(self) -> EconomicHealthScore:
        """
        計算經濟健康評分

        Returns:
            EconomicHealthScore 物件，包含美國、台灣、全球風險評分
        """
        cache_key = "economic_health"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # 取得 FRED 數據
        indicators = self.fred_fetcher.fetch_all_indicators()
        us_economic_result = self.fred_fetcher.calculate_economic_score(indicators)
        us_score = us_economic_result.get("economic_score", 0)

        # === 台灣經濟評分（權重調整） ===
        taiex_price, taiex_change = self._get_taiex_mock_data()
        taiwan_cpi, taiwan_cpi_change = self._get_taiwan_cpi_mock_data()
        twd_rate = self._get_twd_usd_rate_mock_data()

        taiwan_score = 0

        # 股市表現 (30%)
        if taiex_change > 2:
            taiwan_score += 15
        elif taiex_change > 0:
            taiwan_score += 5
        elif taiex_change > -2:
            taiwan_score -= 5
        else:
            taiwan_score -= 15

        # 匯率穩定性 (20%)：強勢 TWD 通常代表經濟強勁
        if 31.5 <= twd_rate <= 32.5:
            taiwan_score += 8
        elif twd_rate < 31.0 or twd_rate > 33.0:
            taiwan_score -= 8

        # 台灣 CPI (30%)
        if taiwan_cpi_change > 0.5:
            taiwan_score -= 12
        elif taiwan_cpi_change > 0:
            taiwan_score -= 5
        elif taiwan_cpi_change < -0.2:
            taiwan_score += 10
        else:
            taiwan_score += 5

        # 全球環境影響 (20%)：用美國 score 作為代理
        taiwan_score += int(us_score * 0.2)

        taiwan_score = max(-100, min(100, taiwan_score))

        # === 全球風險評分 ===
        vix = self._get_vix_mock_data()
        dxy = self._get_dxy_mock_data()
        gold_price = self._get_gold_price_mock_data()

        # 高 VIX = 高風險
        vix_risk = ((vix - 12) / 15) * 50  # 標準化到 -50 ~ +50
        # 強 USD = 可能的全球不穩定
        dxy_risk = ((dxy - 100) / 5) * 20
        # 高金價 = 避險需求
        gold_risk = ((gold_price - 1900) / 300) * 30

        global_risk_score = -(vix_risk + dxy_risk + gold_risk) / 3
        global_risk_score = max(-100, min(100, global_risk_score))

        # === 殖利率曲線狀態 ===
        yield_curve_details = us_economic_result.get("details", {}).get("yield_curve", {})
        spread = yield_curve_details.get("spread", 0)

        if spread < -0.5:
            yield_curve_status = "inverted"
        elif spread < 0:
            yield_curve_status = "inverted"
        elif spread < 0.5:
            yield_curve_status = "flat"
        else:
            yield_curve_status = "normal"

        # === 通膨趨勢 ===
        cpi_details = us_economic_result.get("details", {}).get("cpi", {})
        cpi_change = cpi_details.get("change_pct", 0)

        if isinstance(cpi_change, (int, float)):
            if cpi_change > 0.3:
                inflation_trend = "rising"
            elif cpi_change < -0.2:
                inflation_trend = "falling"
            else:
                inflation_trend = "stable"
        else:
            inflation_trend = "stable"

        result = EconomicHealthScore(
            us_score=round(us_score, 1),
            taiwan_score=round(taiwan_score, 1),
            global_risk_score=round(global_risk_score, 1),
            yield_curve_status=yield_curve_status,
            inflation_trend=inflation_trend,
        )

        self._set_cache(cache_key, result)
        return result

    def detect_market_regime(self) -> MarketRegime:
        """
        偵測市場制度（風險偏好或規避）

        Returns:
            MarketRegime 物件
        """
        cache_key = "market_regime"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # 取得各個指標
        vix = self._get_vix_mock_data()
        health = self.calculate_economic_health()

        indicators = self.fred_fetcher.fetch_all_indicators()
        fed_details = indicators.get("fed_rate", {})
        fed_change = fed_details.get("change", 0)

        # === VIX 水準分類 ===
        if vix < 12:
            vix_level = "low"
        elif vix < 20:
            vix_level = "medium"
        else:
            vix_level = "high"

        # === Fed 方向 ===
        if isinstance(fed_change, (int, float)):
            if fed_change > 0.1:
                fed_direction = "hiking"
            elif fed_change < -0.1:
                fed_direction = "cutting"
            else:
                fed_direction = "neutral"
        else:
            fed_direction = "neutral"

        # === 市場制度綜合判斷 ===
        regime_score = 0

        # 經濟健康 (40%)
        us_health = health.us_score
        regime_score += (us_health / 100) * 40

        # VIX 指標 (30%)：低 VIX = risk_on
        vix_score = (1 - (vix - 10) / 20) * 30
        regime_score += vix_score

        # 殖利率曲線 (20%)
        if health.yield_curve_status == "normal":
            regime_score += 20
        elif health.yield_curve_status == "flat":
            regime_score += 10
        else:
            regime_score -= 20

        # Fed 政策 (10%)
        if fed_direction == "cutting":
            regime_score += 10
        elif fed_direction == "hiking":
            regime_score -= 10

        regime_score = max(-100, min(100, regime_score))

        # 確定制度
        if regime_score > 30:
            regime = "risk_on"
            confidence = 0.8 if regime_score > 50 else 0.6
        elif regime_score < -30:
            regime = "risk_off"
            confidence = 0.8 if regime_score < -50 else 0.6
        else:
            regime = "transitioning"
            confidence = 0.5

        result = MarketRegime(
            regime=regime,
            vix_level=vix_level,
            yield_curve_signal=health.yield_curve_status,
            fed_direction=fed_direction,
            confidence=round(confidence, 2),
        )

        self._set_cache(cache_key, result)
        return result

    def analyze_macro_impact_on_stocks(self, market: str = "us") -> List[SectorImpact]:
        """
        分析宏觀環境對不同扇區的衝擊

        Args:
            market: "us" 或 "taiwan"

        Returns:
            扇區衝擊列表
        """
        cache_key = f"sector_impact_{market}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        health = self.calculate_economic_health()
        regime = self.detect_market_regime()

        indicators = self.fred_fetcher.fetch_all_indicators()
        fed_details = indicators.get("fed_rate", {})
        fed_value = fed_details.get("latest_value", 3.5)
        us2y = indicators.get("us2y_yield", {}).get("latest_value", 4.0)

        impacts = []

        if market == "us":
            # 高利率環境 → 對成長股不利，對銀行有利
            if isinstance(fed_value, (int, float)) and fed_value > 4.5:
                impacts.append(SectorImpact(
                    sector="Technology",
                    impact="negative",
                    score=-25,
                    rationale="高利率提高 DCF 折現率，壓低成長股估值"
                ))
                impacts.append(SectorImpact(
                    sector="Financials",
                    impact="positive",
                    score=25,
                    rationale="高利率擴大淨利差，提高銀行獲利"
                ))
                impacts.append(SectorImpact(
                    sector="Growth",
                    impact="negative",
                    score=-20,
                    rationale="高利率環境對高 PEG 成長股不利"
                ))
            else:
                impacts.append(SectorImpact(
                    sector="Technology",
                    impact="positive",
                    score=20,
                    rationale="低利率有利於成長型科技公司估值"
                ))
                impacts.append(SectorImpact(
                    sector="Financials",
                    impact="negative",
                    score=-15,
                    rationale="低利率壓低淨利差，不利銀行"
                ))

            # 通膨狀況
            if health.inflation_trend == "rising":
                impacts.append(SectorImpact(
                    sector="Energy",
                    impact="positive",
                    score=20,
                    rationale="通膨上升通常伴隨能源價格上漲"
                ))
                impacts.append(SectorImpact(
                    sector="Utilities",
                    impact="negative",
                    score=-15,
                    rationale="公用事業利潤受通膨侵蝕"
                ))
            else:
                impacts.append(SectorImpact(
                    sector="Energy",
                    impact="negative",
                    score=-15,
                    rationale="通膨下降或穩定，能源需求較弱"
                ))
                impacts.append(SectorImpact(
                    sector="Utilities",
                    impact="positive",
                    score=15,
                    rationale="通膨穩定，防守性產業受青睞"
                ))

            # 市場制度
            if regime.regime == "risk_on":
                impacts.append(SectorImpact(
                    sector="Consumer Discretionary",
                    impact="positive",
                    score=20,
                    rationale="風險偏好上升，消費自由裁量支出增加"
                ))
            else:
                impacts.append(SectorImpact(
                    sector="Consumer Discretionary",
                    impact="negative",
                    score=-20,
                    rationale="風險規避，消費者減少非必需支出"
                ))

            # 其他扇區
            impacts.append(SectorImpact(
                sector="Healthcare",
                impact="neutral",
                score=0,
                rationale="防守性扇區，相對獨立於宏觀環境"
            ))
            impacts.append(SectorImpact(
                sector="Materials",
                impact="neutral" if health.us_score > 0 else "negative",
                score=10 if health.us_score > 0 else -10,
                rationale="經濟強勁時，原物料需求增加" if health.us_score > 0 else "經濟疲弱，原物料需求下降"
            ))

        elif market == "taiwan":
            # 台灣 - 出口導向經濟，對全球成長敏感
            global_risk = health.global_risk_score

            impacts.append(SectorImpact(
                sector="Semiconductors (TSMC)",
                impact="positive" if global_risk < 0 else "negative",
                score=25 if global_risk < 0 else -15,
                rationale="全球需求強勁，台積電受益" if global_risk < 0 else "全球風險上升，科技需求下滑"
            ))

            impacts.append(SectorImpact(
                sector="Electronics",
                impact="positive" if health.us_score > 0 else "negative",
                score=20 if health.us_score > 0 else -15,
                rationale="美國經濟強勁有利電子業出口" if health.us_score > 0 else "美國經濟衰退，電子產品需求減弱"
            ))

            # TWD 升值對出口不利
            twd_rate = self._get_twd_usd_rate_mock_data()
            if twd_rate < 31.5:
                impacts.append(SectorImpact(
                    sector="Exporters",
                    impact="negative",
                    score=-15,
                    rationale="新台幣升值，出口競爭力下降"
                ))
            else:
                impacts.append(SectorImpact(
                    sector="Exporters",
                    impact="positive",
                    score=15,
                    rationale="新台幣相對穩定，出口環境良好"
                ))

            impacts.append(SectorImpact(
                sector="Finance",
                impact="positive" if fed_value < 4.0 else "neutral",
                score=15 if fed_value < 4.0 else 0,
                rationale="利率環境穩定，銀行獲利相對穩健"
            ))

            impacts.append(SectorImpact(
                sector="Real Estate",
                impact="negative" if fed_value > 4.5 else "positive",
                score=-20 if fed_value > 4.5 else 10,
                rationale="高利率不利房市" if fed_value > 4.5 else "低利率支持房地產"
            ))

        self._set_cache(cache_key, impacts)
        return impacts

    def get_historical_context(self) -> Dict:
        """
        取得歷史背景，比較當前指標與歷史平均值

        Returns:
            包含各指標百分位排名與極值分析的字典
        """
        cache_key = "historical_context"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        indicators = self.fred_fetcher.fetch_all_indicators()
        health = self.calculate_economic_health()
        vix = self._get_vix_mock_data()
        dxy = self._get_dxy_mock_data()

        context = {}

        # === CPI 變化百分位 ===
        cpi_data = indicators.get("cpi", {})
        cpi_change_pct = cpi_data.get("change_pct", 0)
        if isinstance(cpi_change_pct, (int, float)):
            bench = self._historical_benchmarks["cpi_change_pct"]
            percentile = self._calculate_percentile(
                cpi_change_pct,
                bench["mean"],
                bench["std"],
                bench["min"],
                bench["max"]
            )
            context["cpi"] = {
                "current_value": cpi_data.get("latest_value"),
                "change_pct": round(cpi_change_pct, 2),
                "percentile": percentile,
                "assessment": "極高通膨" if percentile > 80 else "高通膨" if percentile > 60 else "正常" if percentile > 40 else "低通膨"
            }

        # === 失業率百分位 ===
        unemp_data = indicators.get("unemployment", {})
        unemp_value = unemp_data.get("latest_value", 4.0)
        if isinstance(unemp_value, (int, float)):
            bench = self._historical_benchmarks["unemployment"]
            percentile = self._calculate_percentile(
                unemp_value,
                bench["mean"],
                bench["std"],
                bench["min"],
                bench["max"]
            )
            context["unemployment"] = {
                "current_value": round(unemp_value, 2),
                "percentile": percentile,
                "assessment": "充分就業" if percentile < 30 else "良好就業" if percentile < 50 else "偏高失業率"
            }

        # === Fed 利率百分位 ===
        fed_data = indicators.get("fed_rate", {})
        fed_value = fed_data.get("latest_value", 3.5)
        if isinstance(fed_value, (int, float)):
            bench = self._historical_benchmarks["fed_rate"]
            percentile = self._calculate_percentile(
                fed_value,
                bench["mean"],
                bench["std"],
                bench["min"],
                bench["max"]
            )
            context["fed_rate"] = {
                "current_value": round(fed_value, 2),
                "percentile": percentile,
                "assessment": "極度寬鬆" if percentile < 20 else "寬鬆" if percentile < 40 else "中性" if percentile < 60 else "緊縮"
            }

        # === 10 年期美債殖利率百分位 ===
        us10y = indicators.get("us10y_yield", {})
        us10y_val = us10y.get("latest_value")
        if isinstance(us10y_val, (int, float)):
            bench = self._historical_benchmarks["us10y_yield"]
            percentile = self._calculate_percentile(
                us10y_val,
                bench["mean"],
                bench["std"],
                bench["min"],
                bench["max"]
            )
            context["us10y_yield"] = {
                "current_value": round(us10y_val, 2),
                "percentile": percentile,
                "assessment": "極低利率" if percentile < 20 else "低利率" if percentile < 40 else "正常" if percentile < 60 else "高利率"
            }

        # === VIX 百分位 ===
        bench_vix = self._historical_benchmarks["vix"]
        percentile_vix = self._calculate_percentile(
            vix,
            bench_vix["mean"],
            bench_vix["std"],
            bench_vix["min"],
            bench_vix["max"]
        )
        context["vix"] = {
            "current_value": round(vix, 2),
            "percentile": percentile_vix,
            "assessment": "極低波動" if percentile_vix < 20 else "低波動" if percentile_vix < 40 else "正常波動" if percentile_vix < 60 else "高波動"
        }

        # === DXY 百分位 ===
        bench_dxy = self._historical_benchmarks["dxy"]
        percentile_dxy = self._calculate_percentile(
            dxy,
            bench_dxy["mean"],
            bench_dxy["std"],
            bench_dxy["min"],
            bench_dxy["max"]
        )
        context["dxy"] = {
            "current_value": round(dxy, 2),
            "percentile": percentile_dxy,
            "assessment": "美元極弱" if percentile_dxy < 20 else "美元偏弱" if percentile_dxy < 40 else "美元正常" if percentile_dxy < 60 else "美元強勢"
        }

        context["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self._set_cache(cache_key, context)
        return context

    def _calculate_percentile(
        self,
        value: float,
        mean: float,
        std: float,
        min_val: float,
        max_val: float
    ) -> int:
        """
        估算百分位排名（簡化實裝）
        使用 Z-score 與範圍來估算

        Returns:
            0-100 的百分位
        """
        if value <= min_val:
            return 5
        if value >= max_val:
            return 95

        # 正規化到 0-1
        normalized = (value - min_val) / (max_val - min_val)
        percentile = int(normalized * 100)
        return max(5, min(95, percentile))

    def get_dashboard_data(self) -> Dict:
        """
        取得儀表板所需的全部數據

        Returns:
            包含所有指標、評分、市場制度、衝擊分析的完整字典
        """
        cache_key = "dashboard_data"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        # 取得所有組件數據
        indicators = self.fred_fetcher.fetch_all_indicators()
        us_economic = self.fred_fetcher.calculate_economic_score(indicators)
        health = self.calculate_economic_health()
        regime = self.detect_market_regime()
        us_impacts = self.analyze_macro_impact_on_stocks("us")
        taiwan_impacts = self.analyze_macro_impact_on_stocks("taiwan")
        historical = self.get_historical_context()

        # === 全球資產價格 ===
        vix = self._get_vix_mock_data()
        dxy = self._get_dxy_mock_data()
        gold = self._get_gold_price_mock_data()
        oil = self._get_oil_wti_mock_data()
        taiex_price, taiex_change = self._get_taiex_mock_data()
        twd_rate = self._get_twd_usd_rate_mock_data()
        taiwan_cpi, taiwan_cpi_change = self._get_taiwan_cpi_mock_data()

        # === 組合儀表板數據 ===
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "cache_expires_in_seconds": self.cache_ttl,

            # 健康評分
            "economic_health": {
                "us_score": health.us_score,
                "taiwan_score": health.taiwan_score,
                "global_risk_score": health.global_risk_score,
                "yield_curve_status": health.yield_curve_status,
                "inflation_trend": health.inflation_trend,
            },

            # 市場制度
            "market_regime": {
                "regime": regime.regime,
                "vix_level": regime.vix_level,
                "yield_curve_signal": regime.yield_curve_signal,
                "fed_direction": regime.fed_direction,
                "confidence": regime.confidence,
            },

            # 美國經濟指標
            "us_indicators": {
                "cpi": indicators.get("cpi", {}),
                "unemployment": indicators.get("unemployment", {}),
                "fed_rate": indicators.get("fed_rate", {}),
                "us10y_yield": indicators.get("us10y_yield", {}),
                "us2y_yield": indicators.get("us2y_yield", {}),
                "gdp": indicators.get("gdp", {}),
            },

            # 全球資產
            "global_assets": {
                "vix": {"value": round(vix, 2), "level": regime.vix_level},
                "dxy": {"value": round(dxy, 2), "signal": "美元強勢" if dxy > 102 else "美元中性" if dxy > 98 else "美元偏弱"},
                "gold": {"price": round(gold, 2), "currency": "USD/oz"},
                "wti_crude": {"price": round(oil, 2), "currency": "USD/barrel"},
            },

            # 台灣指標
            "taiwan_indicators": {
                "taiex": {
                    "price": taiex_price,
                    "change_pct": taiex_change,
                },
                "twd_usd": {
                    "rate": twd_rate,
                    "signal": "新台幣升值" if twd_rate < 31.5 else "新台幣貶值",
                },
                "cpi": {
                    "value": taiwan_cpi,
                    "change_pct": taiwan_cpi_change,
                },
            },

            # 扇區衝擊
            "sector_impacts": {
                "us": [asdict(impact) for impact in us_impacts],
                "taiwan": [asdict(impact) for impact in taiwan_impacts],
            },

            # 歷史背景
            "historical_context": historical,

            # 經濟信號
            "us_economic_signal": us_economic.get("economic_signal", ""),
            "key_takeaways": self._generate_key_takeaways(health, regime, us_economic),
        }

        self._set_cache(cache_key, dashboard)
        return dashboard

    def _generate_key_takeaways(
        self,
        health: EconomicHealthScore,
        regime: MarketRegime,
        us_economic: Dict
    ) -> List[str]:
        """
        生成關鍵要點摘要

        Returns:
            AI 生成的摘要列表（實際應使用 LLM，此處為規則型）
        """
        takeaways = []

        # 經濟健康
        if health.us_score > 40:
            takeaways.append("美國經濟強勁，有利於高風險資產")
        elif health.us_score < -40:
            takeaways.append("美國經濟衰退風險上升，建議增加防守性配置")
        else:
            takeaways.append("美國經濟環境中性")

        # 市場制度
        if regime.regime == "risk_on":
            takeaways.append(f"市場風險偏好上升（信心度 {regime.confidence:.0%}），有利於成長股")
        elif regime.regime == "risk_off":
            takeaways.append(f"市場風險規避上升（信心度 {regime.confidence:.0%}），宜轉向防守")
        else:
            takeaways.append("市場制度處於過渡期，波動可能增加")

        # 殖利率曲線
        yield_details = us_economic.get("details", {}).get("yield_curve", {})
        spread = yield_details.get("spread")
        if isinstance(spread, (int, float)):
            if spread < -0.5:
                takeaways.append("殖利率曲線嚴重倒掛，衰退訊號強烈")
            elif spread < 0:
                takeaways.append("殖利率曲線倒掛，需關注經濟衰退風險")
            elif spread < 0.5:
                takeaways.append("殖利率曲線扁平，經濟前景不明確")

        # 通膨
        if health.inflation_trend == "rising":
            takeaways.append("通膨上升，持續升息風險增加")
        elif health.inflation_trend == "falling":
            takeaways.append("通膨下降，未來有降息空間")

        # 台灣
        if health.taiwan_score > 20:
            takeaways.append("台灣經濟表現良好，TAIEX 前景樂觀")
        elif health.taiwan_score < -20:
            takeaways.append("台灣經濟承壓，需留意出口動能")

        return takeaways[:5]  # 限制最多 5 個要點


# 全域實例
macro_dashboard_service = MacroDashboardService()
