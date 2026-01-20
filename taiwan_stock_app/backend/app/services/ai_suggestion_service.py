"""
AI Suggestion Service - 每日投資建議
"""
from typing import Dict
from datetime import date, timedelta
import google.generativeai as genai
import json

from app.data_fetchers import FinMindFetcher
from app.config import settings
from app.services.technical_indicators import TechnicalIndicators


class AISuggestionService:
    """AI 每日建議服務"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.llm = genai.GenerativeModel(settings.AI_MODEL)
        self.model = settings.AI_MODEL

    def collect_stock_data(self, stock_id: str, days: int = 60) -> Dict:
        """收集股票分析所需的所有數據"""
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # 取得各類數據
        prices = self.finmind.get_stock_price(stock_id, start_str, end_str)

        # 標準化欄位名稱 (FinMind 使用 max/min，我們需要 high/low)
        if len(prices) > 0:
            if 'max' in prices.columns:
                prices['high'] = prices['max']
            if 'min' in prices.columns:
                prices['low'] = prices['min']

        institutions = self.finmind.get_institutional_investors(stock_id, start_str, end_str)
        margins = self.finmind.get_margin_trading(stock_id, start_str, end_str)

        # 計算技術指標
        technical = self._calculate_technical_indicators(prices)

        # 計算籌碼面指標
        chip_analysis = self._analyze_chip_data(institutions, margins)

        return {
            "stock_id": stock_id,
            "latest_price": float(prices.iloc[-1]["close"]) if len(prices) > 0 else 0,
            "price_change_5d": self._calculate_change(prices, 5),
            "price_change_20d": self._calculate_change(prices, 20),
            "technical": technical,
            "chip": chip_analysis,
            "prices_summary": prices.tail(10).to_dict("records") if len(prices) > 0 else [],
        }

    def _calculate_technical_indicators(self, prices) -> Dict:
        """計算技術指標（使用新的技術指標類）"""
        if len(prices) < 30:
            return {}

        try:
            # 準備 DataFrame（確保有所有需要的欄位）
            df = prices.copy()
            df['close'] = df['close'].astype(float)
            df['open'] = df['open'].astype(float)
            df['high'] = df['high'].astype(float)
            df['low'] = df['low'].astype(float)
            df['volume'] = df.get('Trading_Volume', df.get('volume', 0)).astype(int)

            # 使用技術指標類計算所有指標
            indicators = TechnicalIndicators.get_latest_indicators(df)

            if not indicators:
                return {}

            # 計算額外的分析
            current_price = df['close'].iloc[-1]
            result = indicators.copy()

            # 添加趨勢分析
            if 'ma5' in indicators and 'ma10' in indicators and 'ma20' in indicators:
                ma5 = indicators['ma5']
                ma10 = indicators['ma10']
                ma20 = indicators['ma20']

                result["price_vs_ma5"] = "above" if current_price > ma5 else "below"
                result["price_vs_ma20"] = "above" if current_price > ma20 else "below"
                result["ma_trend"] = "bullish" if ma5 > ma10 > ma20 else "bearish" if ma5 < ma10 < ma20 else "neutral"

            # 添加 MACD 信號
            if 'macd' in indicators and 'macd_signal' in indicators:
                macd = indicators['macd']
                signal = indicators['macd_signal']
                result["macd_signal"] = "bullish" if macd > signal else "bearish"

            # 添加布林通道位置
            if 'bb_upper' in indicators and 'bb_lower' in indicators and 'bb_middle' in indicators:
                bb_upper = indicators['bb_upper']
                bb_lower = indicators['bb_lower']
                bb_middle = indicators['bb_middle']

                if current_price >= bb_upper:
                    result["bb_position"] = "above_upper"
                elif current_price <= bb_lower:
                    result["bb_position"] = "below_lower"
                elif current_price > bb_middle:
                    result["bb_position"] = "above_middle"
                else:
                    result["bb_position"] = "below_middle"

            # 添加 RSI 信號
            if 'rsi' in indicators:
                rsi = indicators['rsi']
                if rsi >= 70:
                    result["rsi_signal"] = "overbought"
                elif rsi <= 30:
                    result["rsi_signal"] = "oversold"
                else:
                    result["rsi_signal"] = "neutral"

            # 添加 KD 信號
            if 'k' in indicators and 'd' in indicators:
                k = indicators['k']
                d = indicators['d']
                if k > 80 and d > 80:
                    result["kd_signal"] = "overbought"
                elif k < 20 and d < 20:
                    result["kd_signal"] = "oversold"
                else:
                    result["kd_signal"] = "neutral"

                result["kd_cross"] = "golden" if k > d else "dead"

            return result

        except Exception as e:
            print(f"計算技術指標時發生錯誤: {e}")
            return {}

    def _analyze_chip_data(self, institutions, margins) -> Dict:
        """分析籌碼面數據"""
        try:
            if len(institutions) == 0 or len(margins) == 0:
                return {}

            # FinMind格式：columns = ['date', 'stock_id', 'buy', 'name', 'sell']
            # 計算外資買賣超
            foreign_data = institutions[institutions['name'].str.contains('Foreign', na=False)]
            if len(foreign_data) > 0:
                foreign_net_5d = (foreign_data['buy'].sum() - foreign_data['sell'].sum()) / 1000  # 轉為張
            else:
                foreign_net_5d = 0

            # 計算投信買賣超
            trust_data = institutions[institutions['name'].str.contains('Investment', na=False)]
            if len(trust_data) > 0:
                trust_net_5d = (trust_data['buy'].sum() - trust_data['sell'].sum()) / 1000
            else:
                trust_net_5d = 0

            # 融資融券變化
            margin_result = {}
            if len(margins) >= 2:
                try:
                    latest_margin = margins.iloc[-1]
                    first_margin = margins.iloc[0]
                    if 'MarginPurchaseBalance' in margins.columns:
                        margin_change = float(latest_margin["MarginPurchaseBalance"]) - float(first_margin["MarginPurchaseBalance"])
                        margin_result["margin_change_5d"] = int(margin_change)
                        margin_result["margin_trend"] = "increasing" if margin_change > 0 else "decreasing"
                    if 'ShortSaleBalance' in margins.columns:
                        short_change = float(latest_margin["ShortSaleBalance"]) - float(first_margin["ShortSaleBalance"])
                        margin_result["short_change_5d"] = int(short_change)
                except:
                    pass

            return {
                "foreign_net_5d": int(foreign_net_5d),
                "trust_net_5d": int(trust_net_5d),
                "foreign_trend": "buying" if foreign_net_5d > 0 else "selling",
                **margin_result
            }
        except Exception as e:
            # 如果籌碼面數據有問題，返回空字典，不影響整體生成
            print(f"Warning: chip data analysis failed: {e}")
            return {}

    def _calculate_change(self, prices, days: int) -> float:
        """計算N日漲跌幅"""
        if len(prices) < days + 1:
            return 0
        current = float(prices.iloc[-1]["close"])
        past = float(prices.iloc[-days - 1]["close"])
        return round((current - past) / past * 100, 2)

    def generate_suggestion(self, stock_id: str, stock_name: str) -> Dict:
        """生成 AI 投資建議（高風險型經紀人）"""
        # 收集數據
        data = self.collect_stock_data(stock_id)

        # 組合 Prompt（高風險型經紀人角色）
        system_prompt = """你是一位高風險型經紀人，擅長捕捉短中線操作機會。你專精於技術分析、籌碼集中度、量價關係，並以積極的投資風格為客戶尋找高報酬機會。

你的回應必須是有效的 JSON 格式，包含以下欄位：

基本建議：
- suggestion: "BUY" | "SELL" | "HOLD"
- confidence: 0.0 到 1.0 之間的數字，表示建議的信心程度
- reasoning: 詳細的分析理由（字串，200-300字）
- key_factors: 關鍵因素陣列，每個元素包含 category, factor, impact

高風險型經紀人專屬分析：
- entry_price_min: 建議進場價下限（數字）
- entry_price_max: 建議進場價上限（數字）
- target_price: 主要目標價（數字，中性預期）
- stop_loss_price: 嚴格停損價（數字）
- take_profit_targets: 多個停利目標，陣列格式 [
    {"price": 數字, "probability": 0.0-1.0, "description": "保守"},
    {"price": 數字, "probability": 0.0-1.0, "description": "中性"},
    {"price": 數字, "probability": 0.0-1.0, "description": "積極"}
  ]
- risk_level: "HIGH" | "MEDIUM" | "LOW"（評估此交易的風險等級）
- time_horizon: "短線(1-3天)" | "中線(1-2週)" | "長線(1個月以上)"
- predicted_change_percent: 預期漲跌幅 %（可正可負）

分析重點：
1. 技術面突破：關注 MACD、布林通道、KD 黃金交叉等信號
2. 籌碼集中度：外資和投信的連續買超是強烈訊號
3. 量價關係：爆量突破、縮量整理、量價背離
4. 風險管理：明確的進場點、停損點、分批停利策略
5. 操作週期：根據市場環境和技術型態決定持有時間

重要提醒：
- 投資建議僅供參考，不構成投資決策依據
- 高風險操作需嚴格執行停損紀律
- reasoning 中需具體說明技術突破點、籌碼優勢、預期催化劑
- 請只回傳 JSON 格式，不要包含任何其他文字或 markdown 標記"""

        user_prompt = self._build_prompt(stock_id, stock_name, data)
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # 呼叫 Gemini API
        response = self.llm.generate_content(
            full_prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                response_mime_type="application/json",
            )
        )

        # 解析結果
        result = json.loads(response.text)
        result["stock_id"] = stock_id
        result["name"] = stock_name
        result["report_date"] = date.today().isoformat()

        return result

    def _build_prompt(self, stock_id: str, stock_name: str, data: Dict) -> str:
        """組合分析 Prompt（高風險型經紀人版本）"""
        tech = data.get('technical', {})
        chip = data.get('chip', {})

        # 構建詳細的技術分析說明
        tech_summary = []
        if tech:
            # 均線分析
            if 'ma_trend' in tech:
                tech_summary.append(f"均線排列：{tech['ma_trend']} (MA5={tech.get('ma5', 'N/A')}, MA10={tech.get('ma10', 'N/A')}, MA20={tech.get('ma20', 'N/A')})")

            # MACD 分析
            if 'macd' in tech:
                macd_sig = tech.get('macd_signal', 'N/A')
                tech_summary.append(f"MACD信號：{macd_sig} (MACD={tech.get('macd', 'N/A'):.2f}, Signal={tech.get('macd_signal', 'N/A')})")

            # RSI 分析
            if 'rsi' in tech:
                rsi_sig = tech.get('rsi_signal', 'N/A')
                tech_summary.append(f"RSI：{tech.get('rsi', 'N/A'):.1f} ({rsi_sig})")

            # KD 分析
            if 'k' in tech and 'd' in tech:
                kd_sig = tech.get('kd_signal', 'N/A')
                kd_cross = tech.get('kd_cross', 'N/A')
                tech_summary.append(f"KD：K={tech['k']:.1f}, D={tech['d']:.1f} ({kd_sig}, {kd_cross} cross)")

            # 布林通道分析
            if 'bb_position' in tech:
                tech_summary.append(f"布林通道位置：{tech['bb_position']}")

            # 威廉指標
            if 'williams_r' in tech:
                tech_summary.append(f"威廉指標：{tech['williams_r']:.1f}")

        # 構建籌碼面說明
        chip_summary = []
        if chip:
            if 'foreign_net_5d' in chip:
                chip_summary.append(f"外資5日買賣超：{chip['foreign_net_5d']}張 ({chip.get('foreign_trend', 'N/A')})")
            if 'trust_net_5d' in chip:
                chip_summary.append(f"投信5日買賣超：{chip['trust_net_5d']}張")
            if 'margin_change_5d' in chip:
                chip_summary.append(f"融資變化：{chip['margin_change_5d']}張 ({chip.get('margin_trend', 'N/A')})")

        return f"""請分析以下股票並給出高風險型投資建議：

## 股票資訊
- 代碼：{stock_id}
- 名稱：{stock_name}
- 最新收盤價：${data['latest_price']}

## 價格動能
- 近5日漲跌幅：{data['price_change_5d']}%
- 近20日漲跌幅：{data['price_change_20d']}%

## 技術面分析
{chr(10).join('- ' + s for s in tech_summary) if tech_summary else '- 數據不足'}

## 籌碼面分析
{chr(10).join('- ' + s for s in chip_summary) if chip_summary else '- 數據不足'}

## 完整技術指標數據
{json.dumps(tech, ensure_ascii=False, indent=2)}

## 近10日價格數據
{json.dumps(data['prices_summary'][-10:] if data['prices_summary'] else [], ensure_ascii=False, indent=2)}

## 操作策略要求
請根據以上數據，以高風險型經紀人的角度：
1. 判斷是否有明確的技術突破或籌碼優勢
2. 提供具體的進場價位區間（不要太寬，控制在5%以內）
3. 設定三個停利目標（保守/中性/積極），並評估達成機率
4. 設定嚴格停損價（建議在進場價下方5-8%）
5. 評估此交易的風險等級和建議操作週期
6. 在 reasoning 中詳細說明技術突破點、籌碼優勢、風險因素

請回傳 JSON 格式的完整建議。"""
