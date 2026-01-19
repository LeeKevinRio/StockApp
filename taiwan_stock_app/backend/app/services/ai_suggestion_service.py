"""
AI Suggestion Service - 每日投資建議
"""
from typing import Dict
from datetime import date, timedelta
import google.generativeai as genai
import json

from app.data_fetchers import FinMindFetcher
from app.config import settings


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
        """計算技術指標"""
        if len(prices) < 20:
            return {}

        close = prices["close"].astype(float)

        # MA
        ma5 = close.rolling(5).mean().iloc[-1]
        ma10 = close.rolling(10).mean().iloc[-1]
        ma20 = close.rolling(20).mean().iloc[-1]

        # RSI (14日)
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]

        # KD (9日)
        low_9 = prices["low"].astype(float).rolling(9).min()
        high_9 = prices["high"].astype(float).rolling(9).max()
        rsv = (close - low_9) / (high_9 - low_9) * 100
        k = rsv.ewm(com=2, adjust=False).mean().iloc[-1]
        d = rsv.ewm(com=2, adjust=False).mean().ewm(com=2, adjust=False).mean().iloc[-1]

        current_price = close.iloc[-1]

        return {
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "rsi_14": round(rsi, 2),
            "k": round(k, 2),
            "d": round(d, 2),
            "price_vs_ma5": "above" if current_price > ma5 else "below",
            "price_vs_ma20": "above" if current_price > ma20 else "below",
            "ma_trend": "bullish" if ma5 > ma10 > ma20 else "bearish" if ma5 < ma10 < ma20 else "neutral",
        }

    def _analyze_chip_data(self, institutions, margins) -> Dict:
        """分析籌碼面數據"""
        if len(institutions) < 5 or len(margins) < 5:
            return {}

        # 近5日外資買賣超
        recent_inst = institutions.tail(5)
        foreign_net_5d = recent_inst["Foreign_Investor_buy"].sum() - recent_inst["Foreign_Investor_sell"].sum()
        trust_net_5d = recent_inst["Investment_Trust_buy"].sum() - recent_inst["Investment_Trust_sell"].sum()

        # 融資融券變化
        recent_margin = margins.tail(5)
        margin_change = float(recent_margin.iloc[-1]["MarginPurchaseBalance"]) - float(recent_margin.iloc[0]["MarginPurchaseBalance"])
        short_change = float(recent_margin.iloc[-1]["ShortSaleBalance"]) - float(recent_margin.iloc[0]["ShortSaleBalance"])

        return {
            "foreign_net_5d": int(foreign_net_5d),
            "trust_net_5d": int(trust_net_5d),
            "foreign_trend": "buying" if foreign_net_5d > 0 else "selling",
            "margin_change_5d": int(margin_change),
            "short_change_5d": int(short_change),
            "margin_trend": "increasing" if margin_change > 0 else "decreasing",
        }

    def _calculate_change(self, prices, days: int) -> float:
        """計算N日漲跌幅"""
        if len(prices) < days + 1:
            return 0
        current = float(prices.iloc[-1]["close"])
        past = float(prices.iloc[-days - 1]["close"])
        return round((current - past) / past * 100, 2)

    def generate_suggestion(self, stock_id: str, stock_name: str) -> Dict:
        """生成 AI 投資建議"""
        # 收集數據
        data = self.collect_stock_data(stock_id)

        # 組合 Prompt
        system_prompt = """你是一位專業的台股分析師。請根據提供的股票數據，給出客觀的投資建議。

你的回應必須是有效的 JSON 格式，包含以下欄位：
- suggestion: "BUY" | "SELL" | "HOLD"
- confidence: 0.0 到 1.0 之間的數字，表示建議的信心程度
- target_price: 目標價（數字）
- stop_loss_price: 停損價（數字）
- reasoning: 詳細的分析理由（字串，100-200字）
- key_factors: 關鍵因素陣列，每個元素包含 category, factor, impact

重要提醒：
1. 投資建議僅供參考，不構成投資決策依據
2. 請保持客觀中立，不要過度樂觀或悲觀
3. reasoning 中請具體說明數據支持的觀點
4. 請只回傳 JSON 格式，不要包含任何其他文字或 markdown 標記"""

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
        """組合分析 Prompt"""
        return f"""請分析以下股票並給出投資建議：

## 股票資訊
- 代碼：{stock_id}
- 名稱：{stock_name}
- 最新收盤價：{data['latest_price']}

## 價格變化
- 近5日漲跌幅：{data['price_change_5d']}%
- 近20日漲跌幅：{data['price_change_20d']}%

## 技術指標
{json.dumps(data['technical'], ensure_ascii=False, indent=2)}

## 籌碼面分析
{json.dumps(data['chip'], ensure_ascii=False, indent=2)}

## 近10日價格數據
{json.dumps(data['prices_summary'], ensure_ascii=False, indent=2)}

請根據以上數據，給出你的投資建議（JSON格式）。"""
