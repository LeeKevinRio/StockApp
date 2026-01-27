"""
AI Suggestion Service - 每日投資建議
整合技術面、籌碼面、基本面、消息面的完整分析
支援台股(TW)與美股(US)
"""
from typing import Dict, List
from datetime import date, timedelta
import google.generativeai as genai
import json
import asyncio
import pandas as pd

from app.data_fetchers import FinMindFetcher, USStockFetcher
from app.data_fetchers.news_fetcher import NewsFetcher
from app.config import settings
from app.services.technical_indicators import TechnicalIndicators


class AISuggestionService:
    """AI 每日建議服務 - 多面向分析（支援台股與美股）"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        self.us_fetcher = USStockFetcher()
        self.news_fetcher = NewsFetcher()
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.llm = genai.GenerativeModel(settings.AI_MODEL)
        self.model = settings.AI_MODEL

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

        # 美股無籌碼面數據
        chip_analysis = {"data_available": False, "note": "籌碼面數據不適用於美股"}

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
            "technical": technical,
            "chip": chip_analysis,
            "fundamental": fundamental,
            "news_sentiment": news_sentiment,
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
        prices = self.finmind.get_stock_price(stock_id, start_str, end_str)
        if len(prices) > 0:
            if 'max' in prices.columns:
                prices['high'] = prices['max']
            if 'min' in prices.columns:
                prices['low'] = prices['min']

        technical = self._calculate_technical_indicators(prices)

        # ========== 籌碼面數據 ==========
        institutions = self.finmind.get_institutional_investors(stock_id, start_str, end_str)
        margins = self.finmind.get_margin_trading(stock_id, start_str, end_str)
        chip_analysis = self._analyze_chip_data(institutions, margins)

        # ========== 基本面數據 ==========
        fundamental = self._analyze_fundamental_data(stock_id, fundamental_start, end_str)

        # ========== 消息面數據 ==========
        news_sentiment = self._analyze_news_sentiment(stock_id)

        return {
            "stock_id": stock_id,
            "market_region": "TW",
            "currency": "TWD",
            "latest_price": float(prices.iloc[-1]["close"]) if len(prices) > 0 else 0,
            "price_change_5d": self._calculate_change(prices, 5),
            "price_change_20d": self._calculate_change(prices, 20),
            "technical": technical,
            "chip": chip_analysis,
            "fundamental": fundamental,
            "news_sentiment": news_sentiment,
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
            print(f"計算技術指標時發生錯誤: {e}")
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
                    print(f"Error processing margin data: {e}")

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
                latest_rev = revenue.iloc[-1]
                prev_year_rev = revenue.iloc[-13] if len(revenue) >= 13 else revenue.iloc[0]

                result["latest_revenue"] = int(latest_rev.get("revenue", 0))
                yoy = ((latest_rev.get("revenue", 0) - prev_year_rev.get("revenue", 1)) / prev_year_rev.get("revenue", 1)) * 100
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

            # 財務報表 (EPS, ROE等)
            fs_data = self.finmind.get_financial_statements(stock_id, start_date, end_date)
            if len(fs_data) > 0 and 'type' in fs_data.columns:
                # EPS
                eps_rows = fs_data[fs_data['type'] == 'EPS']
                if len(eps_rows) > 0:
                    eps_value = eps_rows.iloc[-1].get('value', 0)
                    if eps_value:
                        result["eps"] = round(float(eps_value), 2)
                        result["eps_evaluation"] = "獲利" if eps_value > 0 else "虧損"

                # ROE
                roe_rows = fs_data[fs_data['type'] == 'ROE']
                if len(roe_rows) > 0:
                    roe_value = roe_rows.iloc[-1].get('value', 0)
                    if roe_value:
                        result["roe"] = round(float(roe_value), 2)
                        result["roe_evaluation"] = (
                            "ROE優異_獲利能力強" if roe_value > 20 else
                            "ROE良好" if roe_value > 10 else
                            "ROE一般" if roe_value > 5 else
                            "ROE偏低"
                        )

                # 毛利率
                gpm_rows = fs_data[fs_data['type'].str.contains('GrossProfit', na=False)]
                if len(gpm_rows) > 0:
                    gpm_value = gpm_rows.iloc[-1].get('value', 0)
                    if gpm_value:
                        result["gross_margin"] = round(float(gpm_value), 2)

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
        """計算基本面評分"""
        score = 0

        # 營收年增率 (權重 25%)
        yoy = fund.get("revenue_yoy", 0)
        if yoy > 30:
            score += 25
        elif yoy > 10:
            score += 15
        elif yoy > 0:
            score += 8
        elif yoy < -30:
            score -= 25
        elif yoy < -10:
            score -= 15
        elif yoy < 0:
            score -= 8

        # 本益比 (權重 20%)
        per = fund.get("per", 0)
        if per > 0:
            if per > 40:
                score -= 20  # 太貴
            elif per > 25:
                score -= 10
            elif per < 10:
                score += 20  # 便宜
            elif per < 15:
                score += 10

        # 股價淨值比 (權重 15%)
        pbr = fund.get("pbr", 0)
        if pbr > 0:
            if pbr > 4:
                score -= 15
            elif pbr < 1:
                score += 15
            elif pbr < 1.5:
                score += 8

        # ROE (權重 20%)
        roe = fund.get("roe", 0)
        if roe > 0:
            if roe > 25:
                score += 20  # 高ROE
            elif roe > 15:
                score += 12
            elif roe > 10:
                score += 6
            elif roe < 5:
                score -= 10

        # EPS (權重 10%)
        eps = fund.get("eps", 0)
        if eps > 5:
            score += 10
        elif eps > 2:
            score += 5
        elif eps > 0:
            score += 2
        elif eps < 0:
            score -= 10

        # 殖利率 (權重 10%)
        div_yield = fund.get("dividend_yield", 0)
        if div_yield > 6:
            score += 10
        elif div_yield > 4:
            score += 6
        elif div_yield > 2:
            score += 3

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
        """分析消息面（新聞情緒）"""
        result = {"data_available": False, "news_count": 0}

        try:
            # 同步方式運行異步函數
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            news_list = loop.run_until_complete(self.news_fetcher.fetch_stock_news(stock_id, limit=10))
            loop.close()

            if not news_list:
                return result

            result["data_available"] = True
            result["news_count"] = len(news_list)

            # 分析每則新聞的情緒
            positive_count = 0
            negative_count = 0
            neutral_count = 0
            news_summaries = []

            for news in news_list[:5]:  # 只分析前5則
                sentiment = self.news_fetcher.analyze_sentiment_simple(
                    news.get('title', ''),
                    news.get('summary', '')
                )

                if sentiment['sentiment'] == 'positive':
                    positive_count += 1
                elif sentiment['sentiment'] == 'negative':
                    negative_count += 1
                else:
                    neutral_count += 1

                news_summaries.append({
                    "title": news.get('title', '')[:50],
                    "sentiment": sentiment['sentiment'],
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

    def _calculate_change(self, prices, days: int) -> float:
        """計算N日漲跌幅"""
        if len(prices) < days + 1:
            return 0
        current = float(prices.iloc[-1]["close"])
        past = float(prices.iloc[-days - 1]["close"])
        return round((current - past) / past * 100, 2)

    def generate_suggestion(self, stock_id: str, stock_name: str, market: str = "TW") -> Dict:
        """
        生成 AI 投資建議（多面向綜合分析）

        Args:
            stock_id: 股票代碼
            stock_name: 股票名稱
            market: 'TW' for Taiwan stocks, 'US' for US stocks
        """
        # 收集所有數據
        data = self.collect_stock_data(stock_id, market=market)

        # 計算綜合評分
        tech_score = data.get('technical', {}).get('technical_score', 0)
        chip_score = data.get('chip', {}).get('chip_score', 0)
        fund_score = data.get('fundamental', {}).get('fundamental_score', 0)
        news_score = data.get('news_sentiment', {}).get('sentiment_score', 0)

        # 加權平均 - 美股無籌碼面，調整權重
        if market == "US":
            # 美股權重: 技術50%, 基本面30%, 消息面20%
            total_score = (tech_score * 0.5) + (fund_score * 0.3) + (news_score * 0.2)
        else:
            # 台股權重: 技術40%, 籌碼30%, 基本面20%, 消息面10%
            total_score = (tech_score * 0.4) + (chip_score * 0.3) + (fund_score * 0.2) + (news_score * 0.1)

        # 組合 Prompt
        system_prompt = self._build_system_prompt(total_score, market)
        user_prompt = self._build_prompt(stock_id, stock_name, data, total_score, market)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # 呼叫 Gemini API
        response = self.llm.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.5,  # 降低溫度使判斷更一致
                response_mime_type="application/json",
            )
        )

        # 解析結果
        result = json.loads(response.text)
        result["stock_id"] = stock_id
        result["name"] = stock_name
        result["market_region"] = market
        result["currency"] = "USD" if market == "US" else "TWD"
        result["report_date"] = date.today().isoformat()

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

        # 添加各面向評分供參考
        result["analysis_scores"] = {
            "technical": tech_score,
            "chip": chip_score if market == "TW" else None,
            "fundamental": fund_score,
            "news_sentiment": news_score,
            "total_weighted": round(total_score, 1)
        }

        return result

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
            analysis_aspects = "技術面、基本面、消息面"
        else:
            market_context = "台股投資分析"
            analysis_aspects = "技術面、籌碼面、基本面、消息面"

        return f"""你是一位激進的高風險投資經紀人，專注於{market_context}。你追求高報酬，敢於果斷做出判斷。

## 強制規則（必須遵守）
綜合評分：{round(total_score, 1)} 分
{bias_hint}

**你必須給出 "{suggested_action}" 建議，信心度必須 >= {min_confidence}**

## 你的風格
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
- MACD 翻多 = 買進訊號

## 回應格式（JSON）
{{
  "suggestion": "{suggested_action}",
  "confidence": {min_confidence} 或更高,
  "reasoning": "200字的果斷分析，語氣要強勢，說明為什麼必須{suggested_action}",
  "key_factors": [
    {{"category": "{analysis_aspects.replace('、', '|')}", "factor": "具體因素", "impact": "positive|negative|neutral"}}
  ],
  "entry_price_min": 建議進場價下限,
  "entry_price_max": 建議進場價上限,
  "target_price": 目標價,
  "stop_loss_price": 停損價,
  "take_profit_targets": [
    {{"price": 數字, "probability": 0.5-0.8, "description": "保守|中性|積極"}}
  ],
  "risk_level": "HIGH",
  "time_horizon": "短線(1-3天)" | "中線(1-2週)",
  "predicted_change_percent": 預期漲跌幅（至少 ±3%）,
  "warnings": ["必要的風險警示"]
}}

重要：suggestion 必須是 "{suggested_action}"，confidence 必須 >= {min_confidence}。不要給 HOLD！"""

    def _build_prompt(self, stock_id: str, stock_name: str, data: Dict, total_score: float, market: str = "TW") -> str:
        """組合分析 Prompt"""
        tech = data.get('technical', {})
        chip = data.get('chip', {})
        fund = data.get('fundamental', {})
        news = data.get('news_sentiment', {})

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

## 基本面詳細數據
- 營收年增率：{fund.get('revenue_yoy', 'N/A')}% ({fund.get('revenue_trend', 'N/A')})
- 本益比(PER)：{fund.get('per', 'N/A')} ({fund.get('per_evaluation', 'N/A')})
- 股價淨值比(PBR)：{fund.get('pbr', 'N/A')} ({fund.get('pbr_evaluation', 'N/A')})
- 每股盈餘(EPS)：{fund.get('eps', 'N/A')}元 ({fund.get('eps_evaluation', 'N/A')})
- 股東權益報酬率(ROE)：{fund.get('roe', 'N/A')}% ({fund.get('roe_evaluation', 'N/A')})
- 殖利率：{fund.get('dividend_yield', 'N/A')}% ({fund.get('dividend_evaluation', 'N/A')})
- 近期現金股利：{fund.get('latest_cash_dividend', 'N/A')}元
- 平均現金股利：{fund.get('avg_cash_dividend', 'N/A')}元（{fund.get('dividend_years', 'N/A')}年）"""

        base_info += f"""

## 消息面詳細數據
- 近期新聞數：{news.get('news_count', 0)}
- 正面新聞：{news.get('positive_news', 0)}則
- 負面新聞：{news.get('negative_news', 0)}則
- 情緒判斷：{news.get('sentiment_signal', 'N/A')}

## 近期新聞標題
{json.dumps(news.get('recent_news', []), ensure_ascii=False, indent=2)}

請根據以上所有數據進行綜合分析，給出客觀的投資建議。"""

        return base_info
