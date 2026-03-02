"""
AI Suggestion Service - 每日投資建議
整合技術面、籌碼面、基本面、消息面的完整分析
支援台股(TW)與美股(US)
支援 AI 備援機制: Gemini -> Groq
"""
from typing import Dict, List, Optional
from datetime import date, timedelta
from google import genai
from google.genai import types as genai_types
import json
import asyncio
import logging
import traceback
import pandas as pd

from app.data_fetchers import FinMindFetcher, USStockFetcher, MacroDataFetcher
from app.data_fetchers.news_fetcher import NewsFetcher
from app.config import settings
from app.services.technical_indicators import TechnicalIndicators
from app.services.trading_calendar import get_calendar_gap_days

logger = logging.getLogger(__name__)

# Groq client (lazy initialization)
_groq_client = None

def get_groq_client():
    """Lazy initialization of Groq client"""
    global _groq_client
    if _groq_client is None and settings.GROQ_API_KEY:
        try:
            from groq import Groq
            _groq_client = Groq(api_key=settings.GROQ_API_KEY)
        except ImportError:
            logger.warning("Groq package not installed. Run: pip install groq")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
    return _groq_client


class AISuggestionService:
    """AI 每日建議服務 - 多面向分析（支援台股與美股）"""

    def __init__(self, subscription_tier: str = 'free', ai_client=None):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        self.us_fetcher = USStockFetcher()
        self.news_fetcher = NewsFetcher()
        self.macro_fetcher = MacroDataFetcher()

        # Select model based on subscription tier
        if subscription_tier == 'pro':
            self.model = settings.AI_MODEL_PRO
        else:
            self.model = settings.AI_MODEL_FREE

        self.gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.subscription_tier = subscription_tier
        # BYOK: 用戶自訂 AI client（若有）
        self.ai_client = ai_client

    @classmethod
    def for_user(cls, user, db=None) -> 'AISuggestionService':
        """
        工廠方法：根據用戶訂閱級別創建服務實例，支援 BYOK

        Args:
            user: User model instance with subscription_tier attribute
            db: 資料庫 session（用於查詢 BYOK 配置）

        Returns:
            AISuggestionService instance configured for user's tier
        """
        from app.services.ai_client_factory import AIClientFactory

        tier = getattr(user, 'subscription_tier', 'free') or 'free'
        # 開發模式強制使用 Pro 模型
        if settings.DEV_FORCE_PRO:
            tier = 'pro'
        ai_client = None
        if db is not None:
            config = AIClientFactory.resolve_config(user, db)
            if config:
                ai_client = AIClientFactory.create_client(config)
        return cls(subscription_tier=tier, ai_client=ai_client)

    def collect_stock_data(self, stock_id: str, days: int = 60, market: str = "TW") -> Dict:
        """
        收集股票分析所需的所有數據（技術面、籌碼面、基本面、消息面）

        Args:
            stock_id: 股票代碼
            days: 分析天數
            market: 'TW' for Taiwan stocks, 'US' for US stocks
        """
        if market == "US":
            return self._collect_us_stock_data(stock_id, days)
        else:
            return self._collect_tw_stock_data(stock_id, days)

    def _collect_us_stock_data(self, stock_id: str, days: int = 60) -> Dict:
        """收集美股分析數據"""
        # ========== 技術面數據 ==========
        price_data = self.us_fetcher.get_stock_price(stock_id, period=f"{days}d")

        if price_data:
            prices = pd.DataFrame(price_data)
        else:
            prices = pd.DataFrame()

        technical = self._calculate_technical_indicators(prices)

        # ========== 基本面數據 (美股用yfinance info) ==========
        stock_info = self.us_fetcher.get_stock_info(stock_id)
        fundamental = self._analyze_us_fundamental_data(stock_info)

        # ========== 消息面數據 ==========
        news_sentiment = self._analyze_us_news_sentiment(stock_id)

        # ========== 宏觀面數據 ==========
        macro_analysis = self._analyze_macro_data()

        # 美股無籌碼面數據
        chip_analysis = {"data_available": False, "note": "籌碼面數據不適用於美股"}

        # ========== 社群情緒數據 ==========
        social_analysis = self._analyze_social_sentiment(stock_id)

        latest_price = 0
        if len(prices) > 0:
            latest_price = float(prices.iloc[-1]["close"])

        return {
            "stock_id": stock_id,
            "market_region": "US",
            "currency": "USD",
            "latest_price": latest_price,
            "price_change_5d": self._calculate_change(prices, 5) if len(prices) > 5 else 0,
            "price_change_20d": self._calculate_change(prices, 20) if len(prices) > 20 else 0,
            "avg_daily_volatility": self._calculate_avg_daily_volatility(prices, 10),
            "recent_daily_returns": self._get_recent_daily_returns(prices, 10),
            "technical": technical,
            "chip": chip_analysis,
            "fundamental": fundamental,
            "news_sentiment": news_sentiment,
            "social": social_analysis,
            "macro": macro_analysis,
            "prices_summary": prices.tail(10).to_dict("records") if len(prices) > 0 else [],
        }

    def _collect_tw_stock_data(self, stock_id: str, days: int = 60) -> Dict:
        """收集台股分析數據"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # 基本面需要更長時間範圍
        fundamental_start = (end_date - timedelta(days=365)).strftime("%Y-%m-%d")

        # ========== 技術面數據 ==========
        try:
            prices = self.finmind.get_stock_price(stock_id, start_str, end_str)
            if len(prices) > 0:
                if 'max' in prices.columns:
                    prices['high'] = prices['max']
                if 'min' in prices.columns:
                    prices['low'] = prices['min']
        except Exception as e:
            logger.error(f"Error getting price data for {stock_id}: {e}")
            prices = pd.DataFrame()

        technical = self._calculate_technical_indicators(prices)

        # ========== 籌碼面數據 ==========
        try:
            institutions = self.finmind.get_institutional_investors(stock_id, start_str, end_str)
        except Exception as e:
            logger.error(f"Error getting institutional data for {stock_id}: {e}")
            institutions = pd.DataFrame()

        try:
            margins = self.finmind.get_margin_trading(stock_id, start_str, end_str)
        except Exception as e:
            logger.error(f"Error getting margin data for {stock_id}: {e}")
            margins = pd.DataFrame()

        chip_analysis = self._analyze_chip_data(institutions, margins)

        # ========== 基本面數據 ==========
        fundamental = self._analyze_fundamental_data(stock_id, fundamental_start, end_str)

        # ========== 消息面數據 ==========
        news_sentiment = self._analyze_news_sentiment(stock_id)

        # ========== 宏觀面數據 ==========
        macro_analysis = self._analyze_macro_data()

        # ========== 社群情緒數據 ==========
        social_analysis = self._analyze_social_sentiment(stock_id)

        return {
            "stock_id": stock_id,
            "market_region": "TW",
            "currency": "TWD",
            "latest_price": float(prices.iloc[-1]["close"]) if len(prices) > 0 else 0,
            "price_change_5d": self._calculate_change(prices, 5),
            "price_change_20d": self._calculate_change(prices, 20),
            "avg_daily_volatility": self._calculate_avg_daily_volatility(prices, 10),
            "recent_daily_returns": self._get_recent_daily_returns(prices, 10),
            "technical": technical,
            "chip": chip_analysis,
            "fundamental": fundamental,
            "news_sentiment": news_sentiment,
            "social": social_analysis,
            "macro": macro_analysis,
            "prices_summary": prices.tail(10).to_dict("records") if len(prices) > 0 else [],
        }

    def _calculate_technical_indicators(self, prices) -> Dict:
        """計算技術指標"""
        if len(prices) < 30:
            return {"data_insufficient": True}

        try:
            df = prices.copy()
            df['close'] = df['close'].astype(float)
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df.get('Trading_Volume', df.get('volume', 0)).astype(int)

            indicators = TechnicalIndicators.get_latest_indicators(df)
            if not indicators:
                return {"data_insufficient": True}

            current_price = df['close'].iloc[-1]
            result = indicators.copy()

            # 均線趨勢
            if all(k in indicators for k in ['ma5', 'ma10', 'ma20']):
                ma5, ma10, ma20 = indicators['ma5'], indicators['ma10'], indicators['ma20']
                result["price_vs_ma5"] = "above" if current_price > ma5 else "below"
                result["price_vs_ma20"] = "above" if current_price > ma20 else "below"
                result["ma_trend"] = "bullish" if ma5 > ma10 > ma20 else "bearish" if ma5 < ma10 < ma20 else "neutral"

            # MACD 信號
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd, signal = indicators['macd'], indicators['macd_signal']
                result["macd_status"] = "bullish" if macd > signal else "bearish"
                result["macd_histogram"] = macd - signal

            # 布林通道
            if all(k in indicators for k in ['bb_upper', 'bb_lower', 'bb_middle']):
                bb_upper, bb_lower = indicators['bb_upper'], indicators['bb_lower']
                if current_price >= bb_upper:
                    result["bb_position"] = "above_upper_危險超買"
                elif current_price <= bb_lower:
                    result["bb_position"] = "below_lower_可能超賣"
                elif current_price > indicators['bb_middle']:
                    result["bb_position"] = "above_middle"
                else:
                    result["bb_position"] = "below_middle"

            # RSI 信號
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi >= 80:
                    result["rsi_signal"] = "severely_overbought_強烈賣出訊號"
                elif rsi >= 70:
                    result["rsi_signal"] = "overbought_超買"
                elif rsi <= 20:
                    result["rsi_signal"] = "severely_oversold_強烈買入訊號"
                elif rsi <= 30:
                    result["rsi_signal"] = "oversold_超賣"
                else:
                    result["rsi_signal"] = "neutral"

            # KD 信號
            if 'k' in indicators and 'd' in indicators:
                k, d = indicators['k'], indicators['d']
                if k > 80 and d > 80:
                    result["kd_signal"] = "overbought_超買區_注意回檔風險"
                elif k < 20 and d < 20:
                    result["kd_signal"] = "oversold_超賣區_可能反彈"
                else:
                    result["kd_signal"] = "neutral"
                result["kd_cross"] = "golden_黃金交叉" if k > d else "dead_死亡交叉"

            # 計算綜合技術面評分 (-100 到 +100)
            tech_score = self._calculate_technical_score(result)
            result["technical_score"] = tech_score
            result["technical_signal"] = (
                "strong_buy" if tech_score >= 60 else
                "buy" if tech_score >= 30 else
                "neutral" if tech_score >= -30 else
                "sell" if tech_score >= -60 else
                "strong_sell"
            )

            return result

        except Exception as e:
            logger.error(f"計算技術指標時發生錯誤: {e}")
            return {"error": str(e)}

    def _calculate_technical_score(self, tech: Dict) -> int:
        """計算技術面綜合評分 (-100 到 +100)"""
        score = 0

        # 均線 (權重 25%)
        if tech.get("ma_trend") == "bullish":
            score += 25
        elif tech.get("ma_trend") == "bearish":
            score -= 25

        # MACD (權重 20%)
        if tech.get("macd_status") == "bullish":
            score += 20
        elif tech.get("macd_status") == "bearish":
            score -= 20

        # RSI (權重 20%)
        rsi_signal = tech.get("rsi_signal", "")
        if "severely_overbought" in rsi_signal:
            score -= 20
        elif "overbought" in rsi_signal:
            score -= 10
        elif "severely_oversold" in rsi_signal:
            score += 20
        elif "oversold" in rsi_signal:
            score += 10

        # KD (權重 20%)
        kd_signal = tech.get("kd_signal", "")
        if "overbought" in kd_signal:
            score -= 15
        elif "oversold" in kd_signal:
            score += 15

        kd_cross = tech.get("kd_cross", "")
        if "golden" in kd_cross:
            score += 5
        elif "dead" in kd_cross:
            score -= 5

        # 布林通道 (權重 15%)
        bb_pos = tech.get("bb_position", "")
        if "above_upper" in bb_pos:
            score -= 15
        elif "below_lower" in bb_pos:
            score += 15

        return max(-100, min(100, score))

    def _analyze_chip_data(self, institutions, margins) -> Dict:
        """分析籌碼面數據"""
        result = {"data_available": False}

        try:
            if len(institutions) == 0:
                return result

            result["data_available"] = True

            # FinMind 回傳格式: date, stock_id, buy, name, sell
            # name 欄位值: Foreign_Investor, Investment_Trust, Dealer_self, Dealer_Hedging

            # 外資買賣超（近5日和近20日）
            foreign_data = institutions[institutions['name'].str.contains('Foreign', na=False)]
            if len(foreign_data) > 0:
                foreign_net_all = (foreign_data['buy'].sum() - foreign_data['sell'].sum()) / 1000
                # 取得最近的日期，篩選近5日
                unique_dates = sorted(foreign_data['date'].unique(), reverse=True)[:5]
                recent_5d = foreign_data[foreign_data['date'].isin(unique_dates)]
                foreign_net_5d = (recent_5d['buy'].sum() - recent_5d['sell'].sum()) / 1000
                result["foreign_net_total"] = int(foreign_net_all)
                result["foreign_net_5d"] = int(foreign_net_5d)
                result["foreign_trend"] = "大量買超" if foreign_net_5d > 1000 else "買超" if foreign_net_5d > 0 else "大量賣超" if foreign_net_5d < -1000 else "賣超"

            # 投信買賣超
            trust_data = institutions[institutions['name'].str.contains('Investment', na=False)]
            if len(trust_data) > 0:
                trust_net_all = (trust_data['buy'].sum() - trust_data['sell'].sum()) / 1000
                unique_dates = sorted(trust_data['date'].unique(), reverse=True)[:5]
                recent_5d = trust_data[trust_data['date'].isin(unique_dates)]
                trust_net_5d = (recent_5d['buy'].sum() - recent_5d['sell'].sum()) / 1000
                result["trust_net_total"] = int(trust_net_all)
                result["trust_net_5d"] = int(trust_net_5d)
                result["trust_trend"] = "大量買超" if trust_net_5d > 500 else "買超" if trust_net_5d > 0 else "大量賣超" if trust_net_5d < -500 else "賣超"

            # 自營商買賣超
            dealer_data = institutions[institutions['name'].str.contains('Dealer', na=False)]
            if len(dealer_data) > 0:
                dealer_net_all = (dealer_data['buy'].sum() - dealer_data['sell'].sum()) / 1000
                unique_dates = sorted(dealer_data['date'].unique(), reverse=True)[:5]
                recent_5d = dealer_data[dealer_data['date'].isin(unique_dates)]
                dealer_net_5d = (recent_5d['buy'].sum() - recent_5d['sell'].sum()) / 1000
                result["dealer_net_total"] = int(dealer_net_all)
                result["dealer_net_5d"] = int(dealer_net_5d)
                result["dealer_trend"] = "買超" if dealer_net_5d > 0 else "賣超"

            # 融資融券
            # FinMind 融資融券欄位: MarginPurchaseBuy, MarginPurchaseSell, MarginPurchaseTodayBalance,
            #                      ShortSaleSell, ShortSaleBuy, ShortSaleTodayBalance
            if len(margins) >= 2:
                try:
                    latest = margins.iloc[-1]
                    first = margins.iloc[0]

                    # 檢查可能的欄位名稱
                    margin_balance_col = None
                    short_balance_col = None

                    for col in ['MarginPurchaseTodayBalance', 'MarginPurchaseBalance']:
                        if col in margins.columns:
                            margin_balance_col = col
                            break

                    for col in ['ShortSaleTodayBalance', 'ShortSaleBalance']:
                        if col in margins.columns:
                            short_balance_col = col
                            break

                    if margin_balance_col:
                        margin_change = float(latest[margin_balance_col] or 0) - float(first[margin_balance_col] or 0)
                        result["margin_balance"] = int(latest[margin_balance_col] or 0)
                        result["margin_change"] = int(margin_change)
                        result["margin_trend"] = "融資增加_散戶看多" if margin_change > 0 else "融資減少_散戶退場"

                    if short_balance_col:
                        short_change = float(latest[short_balance_col] or 0) - float(first[short_balance_col] or 0)
                        result["short_balance"] = int(latest[short_balance_col] or 0)
                        result["short_change"] = int(short_change)
                        result["short_trend"] = "融券增加_看空力道增" if short_change > 0 else "融券減少_空頭回補"
                except Exception as e:
                    logger.error(f"Error processing margin data: {e}")

            # 計算籌碼面評分 (-100 到 +100)
            chip_score = self._calculate_chip_score(result)
            result["chip_score"] = chip_score
            result["chip_signal"] = (
                "strong_buy" if chip_score >= 60 else
                "buy" if chip_score >= 30 else
                "neutral" if chip_score >= -30 else
                "sell" if chip_score >= -60 else
                "strong_sell"
            )

        except Exception as e:
            result["error"] = str(e)

        return result

    def _calculate_chip_score(self, chip: Dict) -> int:
        """計算籌碼面評分"""
        score = 0

        # 外資 (權重 50%)
        foreign_5d = chip.get("foreign_net_5d", 0)
        if foreign_5d > 5000:
            score += 50
        elif foreign_5d > 1000:
            score += 30
        elif foreign_5d > 0:
            score += 15
        elif foreign_5d < -5000:
            score -= 50
        elif foreign_5d < -1000:
            score -= 30
        elif foreign_5d < 0:
            score -= 15

        # 投信 (權重 30%)
        trust_5d = chip.get("trust_net_5d", 0)
        if trust_5d > 1000:
            score += 30
        elif trust_5d > 0:
            score += 15
        elif trust_5d < -1000:
            score -= 30
        elif trust_5d < 0:
            score -= 15

        # 融資融券 (權重 20%) - 融資增加通常是散戶進場，需謹慎
        margin_change = chip.get("margin_change", 0)
        if margin_change > 1000:
            score -= 10  # 融資大增，散戶過度樂觀
        elif margin_change < -1000:
            score += 10  # 融資減少，籌碼沉澱

        return max(-100, min(100, score))

    def _analyze_fundamental_data(self, stock_id: str, start_date: str, end_date: str) -> Dict:
        """分析基本面數據"""
        result = {"data_available": False}

        try:
            # 月營收
            revenue = self.finmind.get_monthly_revenue(stock_id, start_date, end_date)
            if len(revenue) >= 2:
                result["data_available"] = True
                # Sort by date descending to get latest first
                revenue = revenue.sort_values('date', ascending=False)
                latest_rev = revenue.iloc[0]
                prev_month_rev = revenue.iloc[1] if len(revenue) >= 2 else None
                prev_year_rev = revenue.iloc[12] if len(revenue) >= 13 else None

                latest_revenue = latest_rev.get("revenue", 0)
                result["latest_revenue"] = int(latest_revenue)

                # Calculate MoM (月增率)
                if prev_month_rev is not None:
                    prev_month_val = prev_month_rev.get("revenue", 0)
                    if prev_month_val and prev_month_val > 0:
                        mom = ((latest_revenue - prev_month_val) / prev_month_val) * 100
                        result["revenue_mom"] = round(mom, 2)
                        result["revenue_mom_trend"] = "月增大幅成長" if mom > 15 else "月增成長" if mom > 0 else "月減大幅衰退" if mom < -15 else "月減衰退"

                # Calculate YoY (年增率)
                if prev_year_rev is not None:
                    prev_year_val = prev_year_rev.get("revenue", 0)
                    if prev_year_val and prev_year_val > 0:
                        yoy = ((latest_revenue - prev_year_val) / prev_year_val) * 100
                        result["revenue_yoy"] = round(yoy, 2)
                        result["revenue_trend"] = "營收大幅成長" if yoy > 20 else "營收成長" if yoy > 0 else "營收大幅衰退" if yoy < -20 else "營收衰退"

            # 本益比、股價淨值比、殖利率
            per_data = self.finmind.get_per_pbr(stock_id, start_date, end_date)
            if len(per_data) > 0:
                result["data_available"] = True
                latest_per = per_data.iloc[-1]
                per_value = latest_per.get("PER", 0)
                pbr_value = latest_per.get("PBR", 0)
                dividend_yield = latest_per.get("dividend_yield", 0)

                if per_value and per_value > 0:
                    result["per"] = round(float(per_value), 2)
                    result["per_evaluation"] = (
                        "本益比偏高_估值昂貴" if per_value > 30 else
                        "本益比合理偏高" if per_value > 20 else
                        "本益比合理" if per_value > 10 else
                        "本益比偏低_可能被低估"
                    )

                if pbr_value and pbr_value > 0:
                    result["pbr"] = round(float(pbr_value), 2)
                    result["pbr_evaluation"] = (
                        "股價淨值比偏高" if pbr_value > 3 else
                        "股價淨值比合理" if pbr_value > 1 else
                        "股價淨值比偏低_可能被低估"
                    )

                if dividend_yield and dividend_yield > 0:
                    result["dividend_yield"] = round(float(dividend_yield), 2)
                    result["dividend_evaluation"] = (
                        "高殖利率_適合存股" if dividend_yield > 5 else
                        "殖利率不錯" if dividend_yield > 3 else
                        "殖利率一般" if dividend_yield > 1 else
                        "低殖利率"
                    )

            # 財務報表 (EPS, Revenue, GrossProfit, OperatingIncome, NetIncome)
            fs_data = self.finmind.get_financial_statements(stock_id, start_date, end_date)
            quarterly_revenue = None
            gross_profit = None
            operating_income = None
            net_income = None

            if len(fs_data) > 0 and 'type' in fs_data.columns:
                # Get latest date's data
                latest_date = fs_data['date'].max()
                latest_fs = fs_data[fs_data['date'] == latest_date]

                for _, row in latest_fs.iterrows():
                    fs_type = row.get('type', '')
                    value = row.get('value')
                    if value is None:
                        continue

                    if fs_type == 'EPS':
                        eps_value = float(value)
                        result["eps"] = round(eps_value, 2)
                        result["eps_evaluation"] = "獲利" if eps_value > 0 else "虧損"
                    elif fs_type == 'Revenue':
                        quarterly_revenue = float(value)
                    elif fs_type == 'GrossProfit':
                        gross_profit = float(value)
                    elif fs_type == 'OperatingIncome':
                        operating_income = float(value)
                    elif fs_type == 'IncomeAfterTaxes':
                        net_income = float(value)

                # Calculate margins from financial statement data
                if quarterly_revenue and quarterly_revenue > 0:
                    if gross_profit is not None:
                        gross_margin = round((gross_profit / quarterly_revenue) * 100, 2)
                        result["gross_margin"] = gross_margin
                        result["gross_margin_evaluation"] = (
                            "毛利率優異" if gross_margin > 50 else
                            "毛利率良好" if gross_margin > 30 else
                            "毛利率一般" if gross_margin > 15 else
                            "毛利率偏低"
                        )
                    if operating_income is not None:
                        operating_margin = round((operating_income / quarterly_revenue) * 100, 2)
                        result["operating_margin"] = operating_margin
                        result["operating_margin_evaluation"] = (
                            "營業利益率優異" if operating_margin > 30 else
                            "營業利益率良好" if operating_margin > 15 else
                            "營業利益率一般" if operating_margin > 5 else
                            "營業利益率偏低"
                        )
                    if net_income is not None:
                        net_margin = round((net_income / quarterly_revenue) * 100, 2)
                        result["net_margin"] = net_margin
                        result["net_margin_evaluation"] = (
                            "淨利率優異" if net_margin > 25 else
                            "淨利率良好" if net_margin > 10 else
                            "淨利率一般" if net_margin > 3 else
                            "淨利率偏低"
                        )

            # Get balance sheet for ROE/ROA calculation
            try:
                balance_data = self.finmind.get_balance_sheet(stock_id, start_date, end_date)
                if len(balance_data) > 0 and net_income is not None:
                    latest_date = balance_data['date'].max()
                    latest_bs = balance_data[balance_data['date'] == latest_date]

                    total_equity = None
                    total_assets = None

                    for _, row in latest_bs.iterrows():
                        bs_type = row.get('type', '')
                        value = row.get('value')
                        if value is None:
                            continue

                        if bs_type == 'Equity':
                            total_equity = float(value)
                        elif bs_type == 'TotalAssets':
                            total_assets = float(value)

                    # Calculate ROE and ROA (annualized)
                    if total_equity and total_equity > 0:
                        # Annualize quarterly net income (multiply by 4)
                        annual_net_income = net_income * 4
                        roe = round((annual_net_income / total_equity) * 100, 2)
                        result["roe"] = roe
                        result["roe_evaluation"] = (
                            "ROE優異_獲利能力強" if roe > 20 else
                            "ROE良好" if roe > 10 else
                            "ROE一般" if roe > 5 else
                            "ROE偏低"
                        )

                    if total_assets and total_assets > 0:
                        annual_net_income = net_income * 4
                        roa = round((annual_net_income / total_assets) * 100, 2)
                        result["roa"] = roa
                        result["roa_evaluation"] = (
                            "ROA優異_資產運用效率高" if roa > 15 else
                            "ROA良好" if roa > 8 else
                            "ROA一般" if roa > 3 else
                            "ROA偏低"
                        )
            except Exception as e:
                logger.error(f"Error getting balance sheet for {stock_id}: {e}")

            # 股息資料
            div_data = self.finmind.get_dividend(stock_id, start_date, end_date)
            if len(div_data) > 0:
                # 計算近年平均股息
                cash_divs = div_data['CashEarningsDistribution'].fillna(0) + div_data['CashStatutorySurplus'].fillna(0)
                if len(cash_divs) > 0:
                    avg_dividend = cash_divs.mean()
                    latest_dividend = cash_divs.iloc[-1] if len(cash_divs) > 0 else 0
                    result["latest_cash_dividend"] = round(float(latest_dividend), 2)
                    result["avg_cash_dividend"] = round(float(avg_dividend), 2)
                    result["dividend_years"] = len(div_data)

            # 計算基本面評分
            fundamental_score = self._calculate_fundamental_score(result)
            result["fundamental_score"] = fundamental_score
            result["fundamental_signal"] = (
                "strong_buy" if fundamental_score >= 60 else
                "buy" if fundamental_score >= 30 else
                "neutral" if fundamental_score >= -30 else
                "sell" if fundamental_score >= -60 else
                "strong_sell"
            )

        except Exception as e:
            result["error"] = str(e)

        return result

    def _calculate_fundamental_score(self, fund: Dict) -> int:
        """計算基本面評分 - 包含估值指標和獲利能力"""
        score = 0

        # 營收年增率 YoY (權重 12%)
        yoy = fund.get("revenue_yoy", 0)
        if yoy:
            if yoy > 30:
                score += 12
            elif yoy > 10:
                score += 8
            elif yoy > 0:
                score += 4
            elif yoy < -30:
                score -= 12
            elif yoy < -10:
                score -= 8
            elif yoy < 0:
                score -= 4

        # 營收月增率 MoM (權重 8%)
        mom = fund.get("revenue_mom", 0)
        if mom:
            if mom > 20:
                score += 8
            elif mom > 5:
                score += 5
            elif mom > 0:
                score += 2
            elif mom < -20:
                score -= 8
            elif mom < -5:
                score -= 5
            elif mom < 0:
                score -= 2

        # 本益比 (權重 12%)
        per = fund.get("per", 0)
        if per > 0:
            if per > 40:
                score -= 12  # 太貴
            elif per > 25:
                score -= 6
            elif per < 10:
                score += 12  # 便宜
            elif per < 15:
                score += 6

        # 股價淨值比 (權重 10%)
        pbr = fund.get("pbr", 0)
        if pbr > 0:
            if pbr > 4:
                score -= 10
            elif pbr < 1:
                score += 10
            elif pbr < 1.5:
                score += 5

        # ROE (權重 15%)
        roe = fund.get("roe", 0)
        if roe:
            if roe > 25:
                score += 15  # 高ROE
            elif roe > 15:
                score += 10
            elif roe > 10:
                score += 5
            elif roe < 5:
                score -= 8

        # ROA (權重 10%)
        roa = fund.get("roa", 0)
        if roa:
            if roa > 15:
                score += 10
            elif roa > 8:
                score += 6
            elif roa > 3:
                score += 3
            elif roa < 2:
                score -= 5

        # 毛利率 (權重 10%)
        gross_margin = fund.get("gross_margin", 0)
        if gross_margin:
            if gross_margin > 50:
                score += 10
            elif gross_margin > 30:
                score += 6
            elif gross_margin > 15:
                score += 3
            elif gross_margin < 10:
                score -= 5

        # 營業利益率 (權重 10%)
        operating_margin = fund.get("operating_margin", 0)
        if operating_margin:
            if operating_margin > 30:
                score += 10
            elif operating_margin > 15:
                score += 6
            elif operating_margin > 5:
                score += 3
            elif operating_margin < 0:
                score -= 10

        # EPS (權重 8%)
        eps = fund.get("eps", 0)
        if eps > 5:
            score += 8
        elif eps > 2:
            score += 4
        elif eps > 0:
            score += 2
        elif eps < 0:
            score -= 8

        # 殖利率 (權重 7%)
        div_yield = fund.get("dividend_yield", 0)
        if div_yield > 6:
            score += 7
        elif div_yield > 4:
            score += 5
        elif div_yield > 2:
            score += 2

        return max(-100, min(100, score))

    def _analyze_us_fundamental_data(self, stock_info: Dict) -> Dict:
        """分析美股基本面數據（來自 yfinance）"""
        result = {"data_available": False}

        if not stock_info:
            return result

        try:
            result["data_available"] = True

            # 本益比 (P/E Ratio)
            pe_ratio = stock_info.get("pe_ratio")
            if pe_ratio and pe_ratio > 0:
                result["per"] = round(float(pe_ratio), 2)
                result["per_evaluation"] = (
                    "P/E偏高_估值昂貴" if pe_ratio > 35 else
                    "P/E合理偏高" if pe_ratio > 22 else
                    "P/E合理" if pe_ratio > 12 else
                    "P/E偏低_可能被低估"
                )

            # EPS
            eps = stock_info.get("eps")
            if eps:
                result["eps"] = round(float(eps), 2)
                result["eps_evaluation"] = "EPS為正_獲利" if eps > 0 else "EPS為負_虧損"

            # 市值
            market_cap = stock_info.get("market_cap", 0)
            if market_cap:
                market_cap_b = market_cap / 1_000_000_000
                result["market_cap"] = round(market_cap_b, 2)
                result["market_cap_category"] = (
                    "大型股" if market_cap_b > 100 else
                    "中型股" if market_cap_b > 10 else
                    "小型股"
                )

            # 52週高低點
            week_52_high = stock_info.get("52_week_high")
            week_52_low = stock_info.get("52_week_low")
            if week_52_high and week_52_low:
                result["52_week_high"] = round(week_52_high, 2)
                result["52_week_low"] = round(week_52_low, 2)

            # 股息殖利率
            dividend_yield = stock_info.get("dividend_yield")
            if dividend_yield:
                result["dividend_yield"] = round(dividend_yield * 100, 2)
                result["dividend_evaluation"] = (
                    "高殖利率" if dividend_yield > 0.03 else
                    "中等殖利率" if dividend_yield > 0.01 else
                    "低殖利率" if dividend_yield > 0 else
                    "無股息"
                )

            # 產業與部門
            result["industry"] = stock_info.get("industry", "N/A")
            result["sector"] = stock_info.get("sector", "N/A")

            # 計算基本面評分（美股版本）
            fundamental_score = self._calculate_us_fundamental_score(result)
            result["fundamental_score"] = fundamental_score
            result["fundamental_signal"] = (
                "strong_buy" if fundamental_score >= 60 else
                "buy" if fundamental_score >= 30 else
                "neutral" if fundamental_score >= -30 else
                "sell" if fundamental_score >= -60 else
                "strong_sell"
            )

        except Exception as e:
            result["error"] = str(e)

        return result

    def _calculate_us_fundamental_score(self, fund: Dict) -> int:
        """計算美股基本面評分"""
        score = 0

        # 本益比 (權重 40%)
        per = fund.get("per", 0)
        if per > 0:
            if per > 50:
                score -= 40  # 太貴
            elif per > 30:
                score -= 20
            elif per < 12:
                score += 40  # 便宜
            elif per < 18:
                score += 20

        # EPS (權重 30%)
        eps = fund.get("eps", 0)
        if eps > 5:
            score += 30
        elif eps > 2:
            score += 15
        elif eps > 0:
            score += 5
        elif eps < 0:
            score -= 30

        # 股息殖利率 (權重 30%)
        div_yield = fund.get("dividend_yield", 0)
        if div_yield > 4:
            score += 30
        elif div_yield > 2:
            score += 15
        elif div_yield > 0:
            score += 5

        return max(-100, min(100, score))

    def _analyze_us_news_sentiment(self, stock_id: str) -> Dict:
        """分析美股消息面（來自 yfinance 新聞）"""
        result = {"data_available": False, "news_count": 0}

        try:
            news_list = self.us_fetcher.get_company_news(stock_id, limit=10)

            if not news_list:
                return result

            result["data_available"] = True
            result["news_count"] = len(news_list)

            # 簡單情緒分析（基於標題關鍵字）
            positive_keywords = ["surge", "soar", "jump", "gain", "rise", "beat", "strong", "record", "upgrade", "buy"]
            negative_keywords = ["fall", "drop", "plunge", "decline", "miss", "weak", "downgrade", "sell", "concern", "fear"]

            positive_count = 0
            negative_count = 0
            neutral_count = 0
            news_summaries = []

            for news in news_list[:5]:
                title = news.get('title', '').lower()
                sentiment = "neutral"

                # 簡單關鍵字分析
                pos_matches = sum(1 for kw in positive_keywords if kw in title)
                neg_matches = sum(1 for kw in negative_keywords if kw in title)

                if pos_matches > neg_matches:
                    sentiment = "positive"
                    positive_count += 1
                elif neg_matches > pos_matches:
                    sentiment = "negative"
                    negative_count += 1
                else:
                    neutral_count += 1

                news_summaries.append({
                    "title": news.get('title', '')[:60],
                    "sentiment": sentiment,
                    "source": news.get('publisher', '')
                })

            result["positive_news"] = positive_count
            result["negative_news"] = negative_count
            result["neutral_news"] = neutral_count
            result["recent_news"] = news_summaries

            # 計算情緒評分
            total = positive_count + negative_count + neutral_count
            if total > 0:
                sentiment_score = ((positive_count - negative_count) / total) * 100
                result["sentiment_score"] = round(sentiment_score, 1)
                result["sentiment_signal"] = (
                    "very_positive_Bullish" if sentiment_score >= 60 else
                    "positive_Positive" if sentiment_score >= 20 else
                    "neutral_Neutral" if sentiment_score >= -20 else
                    "negative_Bearish" if sentiment_score >= -60 else
                    "very_negative_Very Bearish"
                )
            else:
                result["sentiment_score"] = 0
                result["sentiment_signal"] = "no_data"

        except Exception as e:
            result["error"] = str(e)

        return result

    def _analyze_news_sentiment(self, stock_id: str) -> Dict:
        """分析消息面（新聞情緒）- 優先使用 AI 語意分析"""
        result = {"data_available": False, "news_count": 0}

        try:
            # 同步方式運行異步函數
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            news_list = loop.run_until_complete(self.news_fetcher.fetch_stock_news(stock_id, limit=10))

            if not news_list:
                loop.close()
                return result

            result["data_available"] = True
            result["news_count"] = len(news_list)

            # 優先使用 AI 語意分析
            analysis_news = news_list[:5]
            try:
                analysis_news = loop.run_until_complete(
                    self.news_fetcher.analyze_sentiment_with_ai(analysis_news)
                )
                result["sentiment_method"] = "ai"
            except Exception as e:
                logger.warning(f"AI 語意分析失敗，使用關鍵字分析: {e}")
                result["sentiment_method"] = "keyword"

            loop.close()

            # 統計情緒
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            news_summaries = []

            for news in analysis_news:
                # 優先取 AI 分析結果
                ai_sent = news.get("ai_sentiment")
                if ai_sent:
                    score = ai_sent.get("score", 0)
                    if score > 0.2:
                        sentiment = "positive"
                        positive_count += 1
                    elif score < -0.2:
                        sentiment = "negative"
                        negative_count += 1
                    else:
                        sentiment = "neutral"
                        neutral_count += 1
                else:
                    # fallback 到關鍵字分析
                    simple = self.news_fetcher.analyze_sentiment_simple(
                        news.get('title', ''),
                        news.get('summary', '')
                    )
                    sentiment = simple['sentiment']
                    if sentiment == 'positive':
                        positive_count += 1
                    elif sentiment == 'negative':
                        negative_count += 1
                    else:
                        neutral_count += 1

                news_summaries.append({
                    "title": news.get('title', '')[:50],
                    "sentiment": sentiment,
                    "ai_score": ai_sent.get("score") if ai_sent else None,
                    "source": news.get('source', '')
                })

            result["positive_news"] = positive_count
            result["negative_news"] = negative_count
            result["neutral_news"] = neutral_count
            result["recent_news"] = news_summaries

            # 計算情緒評分
            total = positive_count + negative_count + neutral_count
            if total > 0:
                sentiment_score = ((positive_count - negative_count) / total) * 100
                result["sentiment_score"] = round(sentiment_score, 1)
                result["sentiment_signal"] = (
                    "very_positive_消息面利多" if sentiment_score >= 60 else
                    "positive_偏多" if sentiment_score >= 20 else
                    "neutral_中性" if sentiment_score >= -20 else
                    "negative_偏空" if sentiment_score >= -60 else
                    "very_negative_消息面利空"
                )
            else:
                result["sentiment_score"] = 0
                result["sentiment_signal"] = "no_data"

        except Exception as e:
            result["error"] = str(e)

        return result

    def _analyze_macro_data(self) -> Dict:
        """分析宏觀面數據（VIX、美元指數、美股期貨 + FRED 經濟數據）"""
        try:
            return self.macro_fetcher.calculate_combined_macro_score()
        except Exception as e:
            logger.error(f"宏觀數據分析失敗: {e}")
            return {"macro_score": 0, "macro_signal": "no_data", "details": {}}

    def _analyze_social_sentiment(self, stock_id: str, db=None) -> Dict:
        """分析社群情緒數據（PTT, Dcard, Mobile01）"""
        result = {
            "social_score": 0,
            "social_signal": "no_data",
            "total_mentions": 0,
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "avg_score": 0.0,
            "platforms": [],
            "top_topics": [],
        }

        try:
            if db is not None:
                from app.services.sentiment_service import sentiment_service
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        social_data = pool.submit(
                            asyncio.run,
                            sentiment_service.get_social_sentiment_for_ai(db, stock_id)
                        ).result(timeout=15)
                else:
                    social_data = asyncio.run(
                        sentiment_service.get_social_sentiment_for_ai(db, stock_id)
                    )

                if social_data and social_data.get('total_mentions', 0) > 0:
                    result.update(social_data)
                    avg = social_data.get('avg_score', 0)
                    # 將 -1~1 的情緒分數轉換為 -100~100 的評分
                    result['social_score'] = round(avg * 100, 1)
                    if avg > 0.3:
                        result['social_signal'] = 'very_positive'
                    elif avg > 0.1:
                        result['social_signal'] = 'positive'
                    elif avg < -0.3:
                        result['social_signal'] = 'very_negative'
                    elif avg < -0.1:
                        result['social_signal'] = 'negative'
                    else:
                        result['social_signal'] = 'neutral'
            else:
                # 無 DB 時直接從爬蟲取資料
                from app.data_fetchers.taiwan_social_fetcher import taiwan_social_fetcher
                posts = taiwan_social_fetcher.fetch_stock_discussions(stock_id, limit=20)
                if posts:
                    pos = sum(1 for p in posts if p.get('sentiment') == 'positive')
                    neg = sum(1 for p in posts if p.get('sentiment') == 'negative')
                    total = len(posts)
                    scores = [p.get('sentiment_score', 0) for p in posts if p.get('sentiment_score') is not None]
                    avg = sum(scores) / len(scores) if scores else 0

                    result['total_mentions'] = total
                    result['positive'] = pos
                    result['negative'] = neg
                    result['neutral'] = total - pos - neg
                    result['avg_score'] = round(avg, 2)
                    result['social_score'] = round(avg * 100, 1)
                    result['social_signal'] = 'positive' if avg > 0.1 else ('negative' if avg < -0.1 else 'neutral')

        except Exception as e:
            logger.error(f"社群情緒分析失敗: {e}")

        return result

    def _calculate_change(self, prices, days: int) -> float:
        """計算N日漲跌幅"""
        if len(prices) < days + 1:
            return 0
        current = float(prices.iloc[-1]["close"])
        past = float(prices.iloc[-days - 1]["close"])
        return round((current - past) / past * 100, 2)

    def _calculate_avg_daily_volatility(self, prices, days: int = 10) -> float:
        """計算近N日平均日波動率（每日 abs(日報酬率) 的平均值）"""
        if len(prices) < 2:
            return 1.0
        try:
            closes = prices['close'].astype(float).values
            n = min(days + 1, len(closes))
            recent = closes[-n:]
            daily_returns = [abs((recent[i] - recent[i - 1]) / recent[i - 1]) * 100
                            for i in range(1, len(recent)) if recent[i - 1] != 0]
            if not daily_returns:
                return 1.0
            return round(sum(daily_returns) / len(daily_returns), 2)
        except Exception:
            return 1.0

    def _get_recent_daily_returns(self, prices, days: int = 10) -> list:
        """取得近N日每日漲跌幅（帶正負號），供 AI 判斷個股波動特性"""
        if len(prices) < 2:
            return []
        try:
            closes = prices['close'].astype(float).values
            n = min(days + 1, len(closes))
            recent = closes[-n:]
            return [round((recent[i] - recent[i - 1]) / recent[i - 1] * 100, 2)
                    for i in range(1, len(recent)) if recent[i - 1] != 0]
        except Exception:
            return []

    def _generate_mock_suggestion(self, stock_id: str, stock_name: str, market: str = "TW", data: Dict = None) -> Dict:
        """
        Generate a mock suggestion when API/data is unavailable.
        根據 tech_score + chip_score 推導方向，根據 avg_daily_volatility 計算幅度。
        信心度根據指標一致性計算，明確標記 ai_provider = "Mock"。
        """
        import hashlib

        # 使用 stock_id 和日期作為種子，讓同一股票同一天返回一致的結果
        seed_str = f"{stock_id}_{date.today().isoformat()}"
        seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)

        # 從數據推導方向和幅度
        tech_score = 0
        chip_score = 0
        fund_score = 0
        news_score = 0
        macro_score = 0
        social_score = 0
        avg_vol = 1.0
        latest_price = 0

        if data is not None:
            tech_score = data.get('technical', {}).get('technical_score', 0) or 0
            chip_score = data.get('chip', {}).get('chip_score', 0) or 0
            fund_score = data.get('fundamental', {}).get('fundamental_score', 0) or 0
            news_score = data.get('news_sentiment', {}).get('sentiment_score', 0) or 0
            macro_score = data.get('macro', {}).get('macro_score', 0) or 0
            social_score = data.get('social', {}).get('social_score', 0) or 0
            avg_vol = data.get('avg_daily_volatility', 1.0) or 1.0
            latest_price = data.get('latest_price', 0) or 0

        # 交易建議用綜合分數
        if market == "TW":
            combined = tech_score * 0.30 + chip_score * 0.20 + fund_score * 0.15 + news_score * 0.10 + social_score * 0.10 + macro_score * 0.15
        else:
            combined = tech_score * 0.35 + fund_score * 0.25 + news_score * 0.12 + social_score * 0.08 + macro_score * 0.20

        suggestion = "BUY" if combined >= 0 else "SELL"

        # 隔日預測用短期分數（獨立於交易建議）
        if market == "TW":
            pred_score = tech_score * 0.35 + chip_score * 0.35 + news_score * 0.15 + social_score * 0.05 + fund_score * 0.05 + macro_score * 0.05
        else:
            pred_score = tech_score * 0.40 + fund_score * 0.15 + news_score * 0.15 + social_score * 0.05 + macro_score * 0.25

        # 根據 prediction_score 和 avg_daily_volatility 計算預測幅度
        abs_pred = abs(pred_score)
        if abs_pred > 50:
            multiplier = 1.8
        elif abs_pred > 20:
            multiplier = 1.0
        else:
            multiplier = 0.5

        predicted_change = round(avg_vol * multiplier * (1 if pred_score >= 0 else -1), 2)
        next_day_direction = "UP" if predicted_change >= 0 else "DOWN"

        # 信心度根據指標一致性計算
        indicators = [tech_score, chip_score if market == "TW" else macro_score, news_score]
        same_sign = sum(1 for s in indicators if (s > 0) == (pred_score > 0) and s != 0)
        total_nonzero = sum(1 for s in indicators if s != 0)
        if total_nonzero > 0:
            consistency = same_sign / total_nonzero
            confidence = round(0.50 + consistency * 0.15, 2)
        else:
            confidence = 0.50

        mock_price = latest_price if latest_price > 0 else 100.0
        range_margin = 0.015 if market == "TW" else 0.025

        return {
            "stock_id": stock_id,
            "name": stock_name,
            "market_region": market,
            "currency": "USD" if market == "US" else "TWD",
            "report_date": date.today().isoformat(),
            "suggestion": suggestion,
            "confidence": confidence,
            "bullish_probability": confidence if suggestion == "BUY" else (1 - confidence),
            "current_price": mock_price,
            "target_price": round(mock_price * 1.05, 2) if suggestion == "BUY" else round(mock_price * 0.95, 2),
            "stop_loss_price": round(mock_price * 0.97, 2) if suggestion == "BUY" else round(mock_price * 1.03, 2),
            "reasoning": f"[Mock 模式] AI API 暫時無法使用，此為基於技術面+籌碼面評分的數據推導。信心度偏低，僅供參考。股票代碼：{stock_id}",
            "key_factors": [
                {"category": "系統", "factor": "AI API 無法使用，此為 Mock 數據驅動推導", "impact": "neutral"},
                {"category": "數據", "factor": f"技術面: {tech_score}, 籌碼面: {chip_score}, 預測分數: {round(pred_score, 1)}", "impact": "neutral"},
                {"category": "波動", "factor": f"日均波動率: {avg_vol:.2f}%, 預測幅度: {predicted_change:+.2f}%", "impact": "neutral"}
            ],
            "risk_level": "HIGH",
            "time_horizon": "短線(1-3天)",
            "predicted_change_percent": predicted_change,
            "ai_provider": "Mock",
            "next_day_prediction": {
                "direction": next_day_direction,
                "probability": confidence,
                "predicted_change_percent": predicted_change,
                "price_range_low": round(mock_price * (1 + predicted_change / 100 - range_margin), 2),
                "price_range_high": round(mock_price * (1 + predicted_change / 100 + range_margin), 2),
                "reasoning": f"[Mock 模式] prediction_score={round(pred_score, 1)}, 日均波動={avg_vol:.2f}% → 預測 {predicted_change:+.2f}%（信心度低，僅供參考）"
            },
            "analysis_scores": {
                "technical": tech_score,
                "chip": chip_score if market == "TW" else None,
                "fundamental": fund_score,
                "news_sentiment": news_score,
                "social_sentiment": social_score,
                "macro": macro_score,
                "total_weighted": round(combined, 1),
                "prediction_score": round(pred_score, 1),
                "avg_daily_volatility": avg_vol
            }
        }

    def _get_prediction_history_context(self, stock_id: str, db=None) -> str:
        """取得過去預測歷史，作為 AI 回饋參考（含方向偏差和幅度偏差偵測）"""
        if db is None:
            return ""

        try:
            from app.models import PredictionRecord
            records = db.query(PredictionRecord).filter(
                PredictionRecord.stock_id == stock_id,
                PredictionRecord.actual_close_price.isnot(None)
            ).order_by(PredictionRecord.target_date.desc()).limit(10).all()

            if not records:
                return ""

            lines = ["## 過去預測回饋（請參考以改善準確度）"]
            total_error = 0
            direction_correct_count = 0
            up_count = 0
            down_count = 0
            pred_abs_sum = 0
            actual_abs_sum = 0

            for r in reversed(records):
                pred_change = float(r.predicted_change_percent or 0)
                actual_change = float(r.actual_change_percent or 0)
                error = float(r.error_percent or 0)
                correct = "正確" if r.direction_correct else "錯誤"
                total_error += error
                if r.direction_correct:
                    direction_correct_count += 1
                if pred_change >= 0:
                    up_count += 1
                else:
                    down_count += 1
                pred_abs_sum += abs(pred_change)
                actual_abs_sum += abs(actual_change)
                lines.append(
                    f"- {r.target_date}: 預測 {pred_change:+.2f}% → 實際 {actual_change:+.2f}%（方向{correct}，誤差 {error:.2f}%）"
                )

            n = len(records)
            avg_error = total_error / n
            direction_accuracy = direction_correct_count / n

            # 幅度偏差偵測
            if avg_error > 3:
                lines.append(f"\n**⚠️ 幅度偏差嚴重：過去平均誤差 {avg_error:.1f}%，預測幅度明顯過大！請大幅縮小預測範圍，使用 avg_daily_volatility 作為基準。**")
            elif avg_error > 1.5:
                lines.append(f"\n過去平均誤差 {avg_error:.1f}%，請微調預測幅度使其更接近實際波動。")

            # 幅度倍率偵測
            if actual_abs_sum > 0:
                amplitude_ratio = pred_abs_sum / actual_abs_sum
                if amplitude_ratio > 1.5:
                    lines.append(f"**⚠️ 預測幅度平均是實際的 {amplitude_ratio:.1f} 倍！請將預測幅度縮小至目前的 {1/amplitude_ratio:.0%}。**")

            # 方向偏差偵測
            dominant_dir = "UP" if up_count > down_count else "DOWN"
            dominant_pct = max(up_count, down_count) / n
            if dominant_pct > 0.7 and direction_accuracy < 0.5:
                lines.append(f"**⚠️ 方向偏差：過去 {n} 次預測中 {dominant_pct:.0%} 預測 {dominant_dir}，但方向準確率僅 {direction_accuracy:.0%}。請重新評估方向判斷，不要偏向單一方向！**")

            # 整體準確度摘要
            lines.append(f"\n統計摘要：{n} 筆記錄，方向準確率 {direction_accuracy:.0%}，平均誤差 {avg_error:.1f}%")

            return "\n".join(lines)
        except Exception as e:
            logger.warning(f"Failed to get prediction history: {e}")
            return ""

    def _get_holiday_gap_context(self, market: str = "TW") -> str:
        """取得長假 gap 資訊，提醒 AI 調整預測幅度"""
        try:
            gap = get_calendar_gap_days(market=market)
        except Exception:
            return ""

        if gap >= 4:
            market_label = "台股" if market == "TW" else "美股"
            if market == "TW":
                range_hint = "±3%~±5%（台股），極端情況可達 ±5%~±8%"
            else:
                range_hint = "±2%~±4%（美股），極端情況可達 ±3%~±6%"
            return (
                f"\n## ⚠️ 長假缺口提醒\n"
                f"- 上一個交易日到下一個交易日相隔 **{gap} 天**（長假後開盤）\n"
                f"- {market_label}長假後首日通常波動放大 1.5x~2.5x\n"
                f"- 建議預測幅度範圍：{range_hint}\n"
                f"- 請將預測幅度乘以 1.5~2.0 倍修正\n"
            )
        return ""

    def generate_suggestion(self, stock_id: str, stock_name: str, market: str = "TW", db=None) -> Dict:
        """
        生成 AI 投資建議（多面向綜合分析）
        支援備援機制: Gemini -> Groq -> Mock

        Args:
            stock_id: 股票代碼
            stock_name: 股票名稱
            market: 'TW' for Taiwan stocks, 'US' for US stocks
            db: Database session (optional, for prediction history feedback)
        """
        try:
            # 收集所有數據
            data = self.collect_stock_data(stock_id, market=market)
            data['_db'] = db  # 傳遞 db 給 prompt builder 用

            # 計算綜合評分
            tech_score = data.get('technical', {}).get('technical_score', 0)
            chip_score = data.get('chip', {}).get('chip_score', 0)
            fund_score = data.get('fundamental', {}).get('fundamental_score', 0)
            news_score = data.get('news_sentiment', {}).get('sentiment_score', 0)
            social_score = data.get('social', {}).get('social_score', 0)
            macro_score = data.get('macro', {}).get('macro_score', 0)

            # 加權平均 - 6維度（含社群情緒）— 用於交易建議（BUY/SELL）
            if market == "US":
                # 美股權重: 技術35%, 基本面25%, 消息面12%, 社群8%, 宏觀面20%
                total_score = (tech_score * 0.35) + (fund_score * 0.25) + (news_score * 0.12) + (social_score * 0.08) + (macro_score * 0.20)
            else:
                # 台股權重: 技術30%, 籌碼20%, 基本面15%, 消息面10%, 社群10%, 宏觀面15%
                total_score = (tech_score * 0.30) + (chip_score * 0.20) + (fund_score * 0.15) + (news_score * 0.10) + (social_score * 0.10) + (macro_score * 0.15)

            # 隔日預測專用加權評分 — 側重短期因子
            if market == "US":
                # 美股預測權重: 技術40%, 基本面15%, 消息面15%, 社群5%, 宏觀25%
                prediction_score = (tech_score * 0.40) + (fund_score * 0.15) + (news_score * 0.15) + (social_score * 0.05) + (macro_score * 0.25)
            else:
                # 台股預測權重: 技術35%, 籌碼35%, 消息面15%, 社群5%, 基本面5%, 宏觀5%
                prediction_score = (tech_score * 0.35) + (chip_score * 0.35) + (news_score * 0.15) + (social_score * 0.05) + (fund_score * 0.05) + (macro_score * 0.05)

            data['prediction_score'] = round(prediction_score, 1)

            # 組合 Prompt
            system_prompt = self._build_system_prompt(total_score, market)
            user_prompt = self._build_prompt(stock_id, stock_name, data, total_score, market)
            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # 嘗試呼叫 AI API (Gemini -> Groq -> Mock)
            result = self._call_ai_with_fallback(full_prompt, stock_id, stock_name, market)

            if result is None:
                # All AI providers failed, return mock（傳入 data 以利數據驅動）
                return self._generate_mock_suggestion(stock_id, stock_name, market, data=data)

            result["stock_id"] = stock_id
            result["name"] = stock_name
            result["market_region"] = market
            result["currency"] = "USD" if market == "US" else "TWD"
            result["report_date"] = date.today().isoformat()

            latest_price = data.get("latest_price", 0) or 0
            result["current_price"] = latest_price

            # ===== 清理 AI 回傳的百分比格式（可能帶 % 或 + 符號）=====
            def _safe_pct(val, default=0):
                """安全解析百分比值，處理 '+4.85%' 等格式"""
                if val is None:
                    return default
                try:
                    return float(val)
                except (TypeError, ValueError):
                    try:
                        return float(str(val).replace('%', '').strip())
                    except (TypeError, ValueError):
                        return default

            # 清理 result 層級的 predicted_change_percent
            if 'predicted_change_percent' in result:
                result['predicted_change_percent'] = _safe_pct(result['predicted_change_percent'], 3)
            # 清理 next_day_prediction 內的 predicted_change_percent
            _ndp_raw = result.get("next_day_prediction")
            if isinstance(_ndp_raw, dict) and 'predicted_change_percent' in _ndp_raw:
                _ndp_raw['predicted_change_percent'] = _safe_pct(_ndp_raw['predicted_change_percent'], 0)

            # ===== 價格合理性驗證 =====
            # AI 有時會產出完全偏離的 target/stop_loss，在此自動修正
            if latest_price > 0:
                # 台股每日漲跌幅 ±10%，美股無限制但短線不應偏離太多
                max_dev = 0.10 if market == "TW" else 0.20
                for price_key in ("target_price", "stop_loss_price", "entry_price_min", "entry_price_max"):
                    val = result.get(price_key)
                    if val is not None:
                        try:
                            val = float(val)
                            deviation = abs(val - latest_price) / latest_price
                            if deviation > max_dev or val <= 0:
                                # 用公式重算
                                if price_key == "target_price":
                                    pct = float(result.get("predicted_change_percent", 3) or 3)
                                    result[price_key] = round(latest_price * (1 + abs(pct) / 100), 2)
                                elif price_key == "stop_loss_price":
                                    pct = float(result.get("predicted_change_percent", 3) or 3)
                                    result[price_key] = round(latest_price * (1 - abs(pct) / 100), 2)
                                elif price_key == "entry_price_min":
                                    result[price_key] = round(latest_price * 0.98, 2)
                                elif price_key == "entry_price_max":
                                    result[price_key] = round(latest_price * 1.02, 2)
                        except (TypeError, ValueError):
                            pass

                # 修正 take_profit_targets 裡的價格
                tpt = result.get("take_profit_targets")
                if isinstance(tpt, list):
                    for item in tpt:
                        if isinstance(item, dict):
                            p = item.get("price")
                            if p is not None:
                                try:
                                    p = float(p)
                                    if abs(p - latest_price) / latest_price > max_dev or p <= 0:
                                        item["price"] = round(latest_price * 1.05, 2)
                                except (TypeError, ValueError):
                                    pass

                # 修正 next_day_prediction 裡的價格
                ndp = result.get("next_day_prediction")
                range_margin = 0.015 if market == "TW" else 0.025
                if isinstance(ndp, dict):
                    for pk in ("price_range_low", "price_range_high"):
                        pv = ndp.get(pk)
                        if pv is not None:
                            try:
                                pv = float(pv)
                                if abs(pv - latest_price) / latest_price > max_dev or pv <= 0:
                                    pct = float(ndp.get("predicted_change_percent", 0) or 0)
                                    if pk == "price_range_low":
                                        ndp[pk] = round(latest_price * (1 + pct / 100 - range_margin), 2)
                                    else:
                                        ndp[pk] = round(latest_price * (1 + pct / 100 + range_margin), 2)
                            except (TypeError, ValueError):
                                pass

            # ===== 預測幅度校正（防止 AI 所有股票給相似值）=====
            ndp = result.get("next_day_prediction")
            if isinstance(ndp, dict) and latest_price > 0:
                avg_vol = data.get('avg_daily_volatility', 1.0) or 1.0
                pred_score = data.get('prediction_score', 0) or 0
                ai_change = float(ndp.get('predicted_change_percent', 0) or 0)

                # 用 prediction_score 決定信號強度倍數
                abs_score = abs(pred_score)
                if abs_score < 20:
                    multiplier = 0.3 + (abs_score / 20) * 0.3  # 0.3~0.6
                elif abs_score < 50:
                    multiplier = 0.6 + ((abs_score - 20) / 30) * 0.6  # 0.6~1.2
                else:
                    multiplier = 1.2 + min((abs_score - 50) / 50, 1.0) * 0.8  # 1.2~2.0

                # 校正方向：以 prediction_score 決定方向
                direction_sign = 1 if pred_score >= 0 else -1
                # 如果 AI 給出的方向和 prediction_score 一致，保留 AI 的方向
                if ai_change != 0 and (ai_change > 0) == (pred_score >= 0):
                    direction_sign = 1 if ai_change > 0 else -1

                calibrated_change = round(avg_vol * multiplier * direction_sign, 2)

                # 台股限制 ±10%，美股限制 ±20%
                max_change = 10.0 if market == "TW" else 20.0
                calibrated_change = max(-max_change, min(max_change, calibrated_change))

                # 只在 AI 值太雷同（過於接近默認值 ±2~3%）時才用校正值
                if abs(ai_change) < 0.1 or abs(ai_change - calibrated_change) > avg_vol * 0.5:
                    ndp['predicted_change_percent'] = calibrated_change
                    ndp['direction'] = 'UP' if calibrated_change >= 0 else 'DOWN'
                    # 重新計算價格區間
                    range_margin = 0.015 if market == "TW" else 0.025
                    ndp['price_range_low'] = round(latest_price * (1 + calibrated_change / 100 - range_margin), 2)
                    ndp['price_range_high'] = round(latest_price * (1 + calibrated_change / 100 + range_margin), 2)
                    logger.info("預測校正 %s: AI=%.2f%% → 校正=%.2f%% (vol=%.2f%%, score=%.1f)",
                                stock_id, ai_change, calibrated_change, avg_vol, pred_score)

                # 機率也應根據信號強度調整，不要全部 0.70
                if abs_score >= 50:
                    calibrated_prob = round(0.72 + min(abs_score - 50, 50) / 500, 2)  # 0.72~0.82
                elif abs_score >= 20:
                    calibrated_prob = round(0.60 + (abs_score - 20) / 250, 2)  # 0.60~0.72
                else:
                    calibrated_prob = round(0.52 + abs_score / 200, 2)  # 0.52~0.62
                ndp['probability'] = calibrated_prob

            # 強制覆蓋 AI 的建議和信心度（高風險經紀人模式）
            # 根據綜合評分強制設定
            if total_score >= 40:
                result["suggestion"] = "BUY"
                result["confidence"] = max(result.get("confidence", 0), 0.80)
            elif total_score >= 15:
                result["suggestion"] = "BUY"
                result["confidence"] = max(result.get("confidence", 0), 0.70)
            elif total_score >= 0:
                result["suggestion"] = "BUY"
                result["confidence"] = max(result.get("confidence", 0), 0.60)
            elif total_score >= -15:
                result["suggestion"] = "SELL"
                result["confidence"] = max(result.get("confidence", 0), 0.60)
            elif total_score >= -40:
                result["suggestion"] = "SELL"
                result["confidence"] = max(result.get("confidence", 0), 0.70)
            else:
                result["suggestion"] = "SELL"
                result["confidence"] = max(result.get("confidence", 0), 0.80)

            # 確保信心度不低於 0.55
            result["confidence"] = max(result.get("confidence", 0.55), 0.55)

            # 計算看漲機率 (bullish_probability) - 更直覺的指標
            # BUY 建議: 看漲機率 = 信心度
            # SELL 建議: 看漲機率 = 1 - 信心度 (因為 SELL 表示看空)
            confidence = result["confidence"]
            suggestion = result["suggestion"]
            if suggestion == "BUY":
                result["bullish_probability"] = confidence
            elif suggestion == "SELL":
                result["bullish_probability"] = 1 - confidence
            else:  # HOLD
                result["bullish_probability"] = 0.5

            # 設定高風險等級
            result["risk_level"] = "HIGH"

            # 添加各面向評分供參考（6維度）
            result["analysis_scores"] = {
                "technical": tech_score,
                "chip": chip_score if market == "TW" else None,
                "fundamental": fund_score,
                "news_sentiment": news_score,
                "social_sentiment": social_score,
                "macro": macro_score,
                "total_weighted": round(total_score, 1),
                "prediction_score": round(prediction_score, 1),
                "avg_daily_volatility": data.get("avg_daily_volatility", 1.0),
                "latest_price": data.get("latest_price", 0)
            }

            return result

        except Exception as e:
            logger.error(f"Error generating AI suggestion for {stock_id}: {e}\n{traceback.format_exc()}")
            # Return mock suggestion when API fails（盡量傳入 data）
            return self._generate_mock_suggestion(stock_id, stock_name, market, data=locals().get('data'))

    def _call_ai_with_fallback(self, prompt: str, stock_id: str, stock_name: str, market: str) -> Optional[Dict]:
        """
        呼叫 AI API，支援備援機制
        順序: BYOK custom client -> Gemini -> Groq -> None (will use mock)
        """
        # 0. 若有 BYOK 自訂 client，優先使用
        if self.ai_client is not None:
            try:
                byok_result = self.ai_client.generate_json(prompt)
                if byok_result is not None:
                    byok_result["ai_provider"] = self.ai_client.provider_label
                    return byok_result
            except Exception as e:
                logger.warning(f"BYOK client failed for {stock_id}: {e}, falling back to system default")

        # 1. 嘗試 Gemini
        gemini_result = self._call_gemini(prompt)
        if gemini_result is not None:
            gemini_result["ai_provider"] = "Gemini"
            return gemini_result

        # 2. Gemini 失敗，嘗試 Groq
        logger.warning(f"Gemini failed for {stock_id}, trying Groq...")
        groq_result = self._call_groq(prompt)
        if groq_result is not None:
            groq_result["ai_provider"] = "Groq"
            return groq_result

        # 3. 全部失敗
        logger.error(f"All AI providers failed for {stock_id}, will use mock data")
        return None

    def _call_gemini(self, prompt: str) -> Optional[Dict]:
        """呼叫 Gemini API（Pro 模型啟用 thinking 深度推理）"""
        try:
            config = genai_types.GenerateContentConfig(
                temperature=0.3 if self.subscription_tier == 'pro' else 0.2,
                response_mime_type="application/json",
            )
            # Pro 用戶啟用 thinking 模式，提升推理品質
            if self.subscription_tier == 'pro':
                config.thinking_config = genai_types.ThinkingConfig(
                    thinking_budget=2048
                )

            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )
            # 從回應中提取非 thinking 的文字部分
            response_text = ""
            for part in response.candidates[0].content.parts:
                if not getattr(part, 'thought', False):
                    response_text += part.text
            parsed = json.loads(response_text)
            # Gemini 3 有時回傳 JSON array 包裹 → 取第一個元素
            if isinstance(parsed, list):
                if len(parsed) > 0 and isinstance(parsed[0], dict):
                    logger.warning("Gemini returned list instead of dict, extracting first element")
                    parsed = parsed[0]
                else:
                    logger.error(f"Gemini returned unexpected list: {parsed[:100]}")
                    return None
            if not isinstance(parsed, dict):
                logger.error(f"Gemini returned non-dict type: {type(parsed)}")
                return None
            return parsed
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                logger.warning(f"Gemini quota exceeded: {e}")
            else:
                logger.error(f"Gemini API error: {e}")
            return None

    def _call_groq(self, prompt: str) -> Optional[Dict]:
        """呼叫 Groq API"""
        groq_client = get_groq_client()
        if groq_client is None:
            logger.warning("Groq client not available (API key not set or package not installed)")
            return None

        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一位專業的股票分析師，必須以 JSON 格式回覆。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=settings.GROQ_MODEL,
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            response_text = chat_completion.choices[0].message.content
            return json.loads(response_text)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                logger.warning(f"Groq rate limit exceeded: {e}")
            else:
                logger.error(f"Groq API error: {e}")
            return None

    def _build_system_prompt(self, total_score: float, market: str = "TW") -> str:
        """根據綜合評分建立系統提示 - 高風險經紀人風格"""

        # 根據評分給出明確傾向指引和強制信心度
        if total_score >= 40:
            suggested_action = "BUY"
            min_confidence = 0.80
            bias_hint = f"數據強烈偏多！你必須給出 BUY 建議，信心度必須 >= {min_confidence}"
        elif total_score >= 15:
            suggested_action = "BUY"
            min_confidence = 0.65
            bias_hint = f"數據偏多，你應該給出 BUY 建議，信心度應該 >= {min_confidence}"
        elif total_score >= -15:
            # 即使中性，也要根據主導因素做出判斷
            if total_score >= 0:
                suggested_action = "BUY"
                min_confidence = 0.55
                bias_hint = f"數據中性偏多，傾向給 BUY，信心度 >= {min_confidence}"
            else:
                suggested_action = "SELL"
                min_confidence = 0.55
                bias_hint = f"數據中性偏空，傾向給 SELL，信心度 >= {min_confidence}"
        elif total_score >= -40:
            suggested_action = "SELL"
            min_confidence = 0.65
            bias_hint = f"數據偏空，你應該給出 SELL 建議，信心度應該 >= {min_confidence}"
        else:
            suggested_action = "SELL"
            min_confidence = 0.80
            bias_hint = f"數據強烈偏空！你必須給出 SELL 建議，信心度必須 >= {min_confidence}"

        if market == "US":
            market_context = "美股投資分析"
            analysis_aspects = "技術面、基本面、消息面、宏觀面"
        else:
            market_context = "台股投資分析"
            analysis_aspects = "技術面、籌碼面、基本面、消息面、宏觀面"

        # 市場專屬的分析風格
        if market == "US":
            style_section = """## 你的風格（美股）
- 不說「觀望」、「持有」這種模糊的話
- 永遠給出明確的 BUY 或 SELL 方向
- 技術面超買就建議 SELL，超賣就建議 BUY
- 重視基本面（EPS、P/E、營收成長）和宏觀面（Fed 利率、VIX）

## 基本面解讀（美股核心）
- P/E 遠高於同業 + 營收放緩 = 賣出訊號
- EPS 持續成長 + P/E 合理 = 買進訊號
- 市場龍頭（大市值）配合技術面看多 = 強力買進

## 技術面解讀
- KD 死亡交叉 + 超買區 = 立即賣出
- KD 黃金交叉 + 超賣區 = 立即買進
- MACD 翻空 = 賣出訊號
- MACD 翻多 = 買進訊號"""

            # 偵測長假 gap
            try:
                gap_days = get_calendar_gap_days(market=market)
            except Exception:
                gap_days = 1

            holiday_hint_us = ""
            if gap_days >= 4:
                holiday_hint_us = f"""
   - ⚠️ **長假後開盤（休市 {gap_days} 天）**：波動幅度應放大 1.5x~2.5x
   - 長假後預測範圍：±3%~±6%（美股），極端情況可達 ±8%"""

            prediction_section = f"""## 隔日預測計算規則（非常重要！）
你必須根據提供的數據計算每支股票「不同的」隔日預測。
注意：美股交易日為週一至週五，休市日依照 NYSE/NASDAQ 假日。

1. **預測漲跌幅（必須反映該股票的真實波動水準）**：
   - **先觀察「近10日每日漲跌幅」數據**，了解這檔股票實際的日波動量級
   - 美股無漲跌停限制，大型科技股（NVDA/TSLA/AMD等）單日 ±3%~±8% 很常見
   - MEME 股或小型股波動更大，單日可達 ±10%~±20%
   - 穩定藍籌股（AAPL/MSFT/GOOGL）波動較小，通常 ±1%~±3%
   - VIX > 25（高恐慌）：所有股票波動放大 1.5x~2x
   - 財報公布前後：波動可能是平常的 2~3 倍{holiday_hint_us}

2. **預測機率計算**：
   - 多個指標強烈同向：0.70-0.85
   - 多個指標同向：0.60-0.70
   - 指標分歧：0.50-0.55

3. **價格區間計算**：
   - price_range_low = 最新收盤價 × (1 + 預測漲跌幅% - 2.5%)
   - price_range_high = 最新收盤價 × (1 + 預測漲跌幅% + 2.5%)

**嚴禁多檔股票給出相同的預測數值！每支股票波動特性不同，預測值必須不同！**

## 價格計算公式
所有價格都必須基於最新收盤價計算：
- target_price = 最新收盤價 × (1 + 預期漲幅%/100)
- stop_loss_price = 最新收盤價 × (1 - 停損幅%/100)
- entry_price_min = 最新收盤價 × 0.98 ~ 0.99
- entry_price_max = 最新收盤價 × 1.00 ~ 1.02

**所有輸出價格都必須在最新收盤價的 ±15% 範圍內！**"""

            reasoning_hint = f"說明計算依據：RSI=多少、MACD狀態、P/E估值、VIX恐慌指數等"

        else:
            style_section = """## 你的風格（台股）
- 不說「觀望」、「持有」這種模糊的話
- 永遠給出明確的 BUY 或 SELL 方向
- 看到法人賣超就果斷說 SELL
- 看到法人買超就大膽說 BUY
- 技術面超買就建議 SELL，超賣就建議 BUY

## 籌碼面解讀（台股最重要）
- 外資賣超 > 1萬張 = 強烈賣出訊號
- 外資買超 > 1萬張 = 強烈買進訊號
- 三大法人同步買超/賣超 = 必須跟進

## 技術面解讀
- KD 死亡交叉 + 超買區 = 立即賣出
- KD 黃金交叉 + 超賣區 = 立即買進
- MACD 翻空 = 賣出訊號
- MACD 翻多 = 買進訊號"""

            # 偵測長假 gap
            try:
                gap_days = get_calendar_gap_days(market=market)
            except Exception:
                gap_days = 1

            holiday_hint_tw = ""
            if gap_days >= 4:
                holiday_hint_tw = f"""
   - ⚠️ **長假後開盤（休市 {gap_days} 天）**：波動幅度應放大 1.5x~2.5x
   - 長假後預測範圍：±3%~±5%（台股），極端情況可達 ±5%~±8%"""

            prediction_section = f"""## 隔日預測計算規則（非常重要！）
你必須根據提供的數據計算每支股票「不同的」隔日預測。

1. **預測漲跌幅（必須反映該股票的真實波動水準）**：
   - **先觀察「近10日每日漲跌幅」數據**，了解這檔股票實際的日波動量級
   - 台股漲跌停為 ±10%，強勢股可以接近漲停或跌停
   - 高波動股（如生技、IC設計、面板）日波動 ±2%~±5% 很正常
   - 權值股（台積電、聯發科）波動相對較小，通常 ±1%~±3%
   - 小型股/投機股波動更大，可達 ±5%~±10%
   - 外資大量買超（>10000張）+ 技術面看多 = 可能大漲 3%~7%
   - 外資大量賣超（>10000張）+ 技術面看空 = 可能大跌 3%~7%{holiday_hint_tw}

2. **預測機率計算**：
   - 多個指標強烈同向（技術+籌碼+消息）：0.70-0.85
   - 多個指標同向：0.60-0.70
   - 指標分歧：0.50-0.55

3. **價格區間計算**：
   - price_range_low = 最新收盤價 × (1 + 預測漲跌幅% - 1.5%)
   - price_range_high = 最新收盤價 × (1 + 預測漲跌幅% + 1.5%)

**嚴禁多檔股票給出相同的預測數值！每支股票波動特性不同，預測值必須不同！**"""

            reasoning_hint = f"說明計算依據：RSI=多少、外資買賣超多少張、MACD狀態等"

        return f"""你是一位激進的高風險投資經紀人，專注於{market_context}。你追求高報酬，敢於果斷做出判斷。

## 強制規則（必須遵守）
綜合評分：{round(total_score, 1)} 分
{bias_hint}

**你必須給出 "{suggested_action}" 建議，信心度必須 >= {min_confidence}**

{style_section}

## 預測獨立性（極其重要！）
- suggestion（BUY/SELL）= 交易建議，考量中期走勢，必須遵守上方強制規則
- next_day_prediction = 隔日走勢預測，必須獨立判斷，**不受 suggestion 影響**
- 即使 suggestion 是 BUY，若短期超買（RSI>70、KD高檔死叉），next_day_prediction.direction 可以是 DOWN
- 即使 suggestion 是 SELL，若短期超賣（RSI<30、KD低檔金叉），next_day_prediction.direction 可以是 UP
- 隔日預測判斷依據：prediction_score、RSI、MACD、布林通道位置、{'籌碼動向（外資/投信）' if market == 'TW' else 'VIX恐慌指數、宏觀面'}

{prediction_section}

## 回應格式（JSON）
{{
  "suggestion": "{suggested_action}",
  "confidence": {min_confidence} 或更高,
  "reasoning": "200字的果斷分析，語氣要強勢，說明為什麼必須{suggested_action}",
  "key_factors": [
    {{"category": "{analysis_aspects.replace('、', '|')}", "factor": "具體因素", "impact": "positive|negative|neutral"}}
  ],
  "entry_price_min": 建議進場價下限（基於最新收盤價計算）,
  "entry_price_max": 建議進場價上限（基於最新收盤價計算）,
  "target_price": 目標價（基於最新收盤價 + 預期漲幅計算）,
  "stop_loss_price": 停損價（基於最新收盤價 - 風險容忍度計算）,
  "take_profit_targets": [
    {{"price": 數字, "probability": 0.5-0.8, "description": "保守|中性|積極"}}
  ],
  "risk_level": "HIGH",
  "time_horizon": "短線(1-3天)" | "中線(1-2週)",
  "predicted_change_percent": 預期漲跌幅（根據訊號強度：弱訊號 ±0.5-1.5%，中訊號 ±1.5-3%，強訊號 ±3-5%）,
  "next_day_prediction": {{
    "direction": "UP" 或 "DOWN"（獨立判斷，可以與 suggestion 不同！）,
    "probability": 根據指標同向性計算的機率（0.55-0.85）,
    "predicted_change_percent": 根據 prediction_score 和 avg_daily_volatility 計算的具體數值（精確到小數點後兩位，如 +1.23 或 -0.87）,
    "price_range_low": 最新收盤價 × (1 + 預測漲跌幅 - {'1.5%' if market == 'TW' else '2.5%'}),
    "price_range_high": 最新收盤價 × (1 + 預測漲跌幅 + {'1.5%' if market == 'TW' else '2.5%'}),
    "reasoning": "{reasoning_hint}"
  }},
  "warnings": ["必要的風險警示"]
}}

重要：
1. suggestion 必須是 "{suggested_action}"，confidence 必須 >= {min_confidence}。不要給 HOLD！
2. next_day_prediction 是獨立的隔日預測，direction 可以與 suggestion 不同！
3. next_day_prediction 的 predicted_change_percent 必須根據該股票的實際數據計算，每支股票都要不同！
4. 不要給固定值如 -2.5%，要根據 prediction_score 和 avg_daily_volatility 計算合理的預測值！
5. target_price、stop_loss_price、entry_price_min/max 都必須基於最新收盤價計算，不能偏離太遠！"""

    def _build_prompt(self, stock_id: str, stock_name: str, data: Dict, total_score: float, market: str = "TW") -> str:
        """組合分析 Prompt"""
        tech = data.get('technical', {})
        chip = data.get('chip', {})
        fund = data.get('fundamental', {})
        news = data.get('news_sentiment', {})
        macro = data.get('macro', {})

        social = data.get('social', {})
        currency_symbol = "$" if market == "US" else "NT$"
        market_label = "美股" if market == "US" else "台股"

        base_info = f"""## 股票資訊
- 市場：{market_label}
- 代碼：{stock_id}
- 名稱：{stock_name}
- 最新收盤價：{currency_symbol}{data['latest_price']}
- 近5日漲跌幅：{data['price_change_5d']}%
- 近20日漲跌幅：{data['price_change_20d']}%

## 綜合評分（滿分 ±100）
- 技術面評分：{tech.get('technical_score', 'N/A')} → {tech.get('technical_signal', 'N/A')}"""

        if market == "US":
            base_info += f"""
- 籌碼面評分：N/A（美股無此數據）"""
        else:
            base_info += f"""
- 籌碼面評分：{chip.get('chip_score', 'N/A')} → {chip.get('chip_signal', 'N/A')}"""

        base_info += f"""
- 基本面評分：{fund.get('fundamental_score', 'N/A')} → {fund.get('fundamental_signal', 'N/A')}
- 消息面評分：{news.get('sentiment_score', 'N/A')} → {news.get('sentiment_signal', 'N/A')}
- **加權總分：{round(total_score, 1)}**

## 技術面詳細數據
- 均線趨勢：{tech.get('ma_trend', 'N/A')}
- RSI：{tech.get('rsi', 'N/A')} ({tech.get('rsi_signal', 'N/A')})
- KD：K={tech.get('k', 'N/A')}, D={tech.get('d', 'N/A')} ({tech.get('kd_signal', 'N/A')}, {tech.get('kd_cross', 'N/A')})
- MACD：{tech.get('macd_status', 'N/A')}
- 布林通道：{tech.get('bb_position', 'N/A')}"""

        if market == "US":
            # 美股基本面數據
            base_info += f"""

## 基本面詳細數據
- 本益比(P/E)：{fund.get('per', 'N/A')} ({fund.get('per_evaluation', 'N/A')})
- 每股盈餘(EPS)：${fund.get('eps', 'N/A')} ({fund.get('eps_evaluation', 'N/A')})
- 市值：${fund.get('market_cap', 'N/A')}B ({fund.get('market_cap_category', 'N/A')})
- 股息殖利率：{fund.get('dividend_yield', 'N/A')}% ({fund.get('dividend_evaluation', 'N/A')})
- 52週高點：${fund.get('52_week_high', 'N/A')}
- 52週低點：${fund.get('52_week_low', 'N/A')}
- 產業：{fund.get('industry', 'N/A')}
- 部門：{fund.get('sector', 'N/A')}"""
        else:
            # 台股籌碼面和基本面數據
            base_info += f"""

## 籌碼面詳細數據
- 外資5日買賣超：{chip.get('foreign_net_5d', 'N/A')}張 ({chip.get('foreign_trend', 'N/A')})
- 投信5日買賣超：{chip.get('trust_net_5d', 'N/A')}張 ({chip.get('trust_trend', 'N/A')})
- 自營商5日買賣超：{chip.get('dealer_net_5d', 'N/A')}張 ({chip.get('dealer_trend', 'N/A')})
- 融資餘額：{chip.get('margin_balance', 'N/A')}張，變化：{chip.get('margin_change', 'N/A')}張 ({chip.get('margin_trend', 'N/A')})
- 融券餘額：{chip.get('short_balance', 'N/A')}張，變化：{chip.get('short_change', 'N/A')}張 ({chip.get('short_trend', 'N/A')})

## 基本面詳細數據（估值指標）
- 本益比(PER)：{fund.get('per', 'N/A')} ({fund.get('per_evaluation', 'N/A')})
- 股價淨值比(PBR)：{fund.get('pbr', 'N/A')} ({fund.get('pbr_evaluation', 'N/A')})
- 殖利率：{fund.get('dividend_yield', 'N/A')}% ({fund.get('dividend_evaluation', 'N/A')})

## 獲利能力指標
- 每股盈餘(EPS)：{fund.get('eps', 'N/A')}元 ({fund.get('eps_evaluation', 'N/A')})
- 股東權益報酬率(ROE)：{fund.get('roe', 'N/A')}% ({fund.get('roe_evaluation', 'N/A')})
- 資產報酬率(ROA)：{fund.get('roa', 'N/A')}% ({fund.get('roa_evaluation', 'N/A')})
- 毛利率：{fund.get('gross_margin', 'N/A')}% ({fund.get('gross_margin_evaluation', 'N/A')})
- 營業利益率：{fund.get('operating_margin', 'N/A')}% ({fund.get('operating_margin_evaluation', 'N/A')})
- 淨利率：{fund.get('net_margin', 'N/A')}% ({fund.get('net_margin_evaluation', 'N/A')})

## 營收成長
- 營收月增率(MoM)：{fund.get('revenue_mom', 'N/A')}% ({fund.get('revenue_mom_trend', 'N/A')})
- 營收年增率(YoY)：{fund.get('revenue_yoy', 'N/A')}% ({fund.get('revenue_trend', 'N/A')})

## 股利
- 近期現金股利：{fund.get('latest_cash_dividend', 'N/A')}元
- 平均現金股利：{fund.get('avg_cash_dividend', 'N/A')}元（{fund.get('dividend_years', 'N/A')}年）"""

        # 宏觀面數據
        macro_details = macro.get('details', {})
        base_info += f"""

## 宏觀面數據
- 宏觀面評分：{macro.get('macro_score', 'N/A')} → {macro.get('macro_signal', 'N/A')}
- VIX 恐慌指數：{macro_details.get('vix', {}).get('value', 'N/A')} ({macro_details.get('vix', {}).get('signal', 'N/A')})
- 美元指數變化：{macro_details.get('dxy', {}).get('change_pct', 'N/A')}% ({macro_details.get('dxy', {}).get('signal', 'N/A')})
- 美股期貨變化：S&P {macro_details.get('us_futures', {}).get('sp500_change_pct', 'N/A')}%, 納指 {macro_details.get('us_futures', {}).get('nasdaq_change_pct', 'N/A')}% ({macro_details.get('us_futures', {}).get('signal', 'N/A')})
- 10年公債殖利率：{macro_details.get('us10y', {}).get('value', 'N/A')}% ({macro_details.get('us10y', {}).get('signal', 'N/A')})
- 黃金變化：{macro_details.get('gold', {}).get('change_pct', 'N/A')}% ({macro_details.get('gold', {}).get('signal', 'N/A')})

## 消息面詳細數據
- 近期新聞數：{news.get('news_count', 0)}
- 正面新聞：{news.get('positive_news', 0)}則
- 負面新聞：{news.get('negative_news', 0)}則
- 情緒判斷：{news.get('sentiment_signal', 'N/A')}

## 社群輿論數據（PTT/Dcard/Mobile01）
- 社群評分：{social.get('social_score', 'N/A')} → {social.get('social_signal', 'N/A')}
- 總提及數：{social.get('total_mentions', 0)}
- 正面聲量：{social.get('positive', 0)}
- 負面聲量：{social.get('negative', 0)}
- 中性聲量：{social.get('neutral', 0)}
- 平均情緒分數：{social.get('avg_score', 0)}
- 活躍平台：{', '.join(social.get('platforms', [])) or 'N/A'}
- 熱門話題：{', '.join(social.get('top_topics', [])[:3]) or 'N/A'}

## 近期新聞標題
{json.dumps(news.get('recent_news', []), ensure_ascii=False, indent=2)}

## 隔日預測計算參考（獨立於交易建議！）
請根據以下數據**獨立**計算 next_day_prediction（不受 suggestion 方向約束）：
- 最新收盤價：{data['latest_price']}
- **prediction_score（短期加權評分）：{data.get('prediction_score', 0)}**（正值偏多，負值偏空）
- **avg_daily_volatility（日均波動率）：{data.get('avg_daily_volatility', 1.0):.2f}%**
- RSI 值：{tech.get('rsi', 50)}（<30 偏多，>70 偏空）
- {'外資5日淨買賣：' + str(chip.get('foreign_net_5d', 0)) + '張' if market == 'TW' else 'VIX 恐慌指數：' + str(macro.get('details', {}).get('vix', {}).get('value', 'N/A'))}
- MACD 狀態：{tech.get('macd_status', 'N/A')}

**近10日每日實際漲跌幅（從舊到新）：**
{data.get('recent_daily_returns', [])}
觀察上面的數據：這檔股票實際的日波動幅度和模式是什麼？最近是放量還是縮量？趨勢還是震盪？

**預測幅度規則（極重要！）**
- 你的預測幅度必須反映這檔股票**真實的波動水準**，不要給所有股票類似的值！
- 參考上方近10日漲跌幅，如果近期日波動經常在 ±2%~±5%，你的預測也應該在這個量級
- {'台股漲跌停為 ±10%，如果多重強訊號同向，預測可以到 ±5%~±8%' if market == 'TW' else '美股無漲跌停限制，大型科技股單日 ±3%~±8% 很常見，財報日或重大事件可達 ±10%~±15%'}
- **弱訊號**（|prediction_score| < 20，指標分歧）：預測幅度約為日均波動的 0.3~0.6 倍
- **中等訊號**（|prediction_score| 20~50）：預測幅度約為日均波動的 0.6~1.2 倍
- **強訊號**（|prediction_score| > 50，多數指標同向）：預測幅度約為日均波動的 1.2~2.0 倍
- prediction_score > 0 → direction 傾向 UP；< 0 → 傾向 DOWN
- **每支股票的預測值必須不同！不要出現多檔股票預測相同數值的情況！**

{self._get_prediction_history_context(stock_id, data.get('_db'))}

{self._get_holiday_gap_context(market)}

**你的隔日預測必須基於數據計算，預測值要貼近實際日常波動範圍！**

⚠️ 最終檢查（輸出前必讀）：
- 最新收盤價 = {currency_symbol}{data['latest_price']}
- target_price 必須在 {data['latest_price']} 附近（偏離不超過 15%）
- stop_loss_price 必須在 {data['latest_price']} 附近（偏離不超過 15%）
- entry_price_min/max 必須在 {data['latest_price']} 附近（偏離不超過 5%）
- price_range_low/high 必須在 {data['latest_price']} 附近（偏離不超過 5%）

請根據以上所有數據進行綜合分析，給出客觀的投資建議。"""

        return base_info
