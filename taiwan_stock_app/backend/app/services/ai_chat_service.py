"""
AI Chat Service - AI 問答服務
"""
from typing import List, Dict, Optional
from datetime import date, timedelta
import google.generativeai as genai

from app.data_fetchers import FinMindFetcher
from app.config import settings


class AIChatService:
    """AI 問答服務"""

    SYSTEM_PROMPT = """你是一位專業的台股投資顧問 AI 助手。你可以：

1. 回答關於台股投資的各種問題
2. 分析特定股票的技術面、籌碼面、基本面
3. 解釋投資概念和術語
4. 提供市場趨勢分析

重要原則：
- 所有投資建議僅供參考，不構成投資決策依據
- 回答時引用具體數據，說明數據來源
- 保持客觀中立，提醒投資風險
- 如果不確定或沒有相關數據，誠實告知

當用戶詢問特定股票時，你會收到該股票的最新數據，請根據數據提供分析。"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.llm = genai.GenerativeModel(settings.AI_MODEL)
        self.model = settings.AI_MODEL

    def chat(
        self,
        user_message: str,
        stock_id: Optional[str] = None,
        chat_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """處理用戶問答"""
        # 建立對話歷史
        history = []
        if chat_history:
            for msg in chat_history[-10:]:  # 最多保留10輪對話
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})

        # 如果指定股票，取得即時數據
        stock_context = ""
        sources = []
        if stock_id:
            try:
                stock_data = self._get_stock_context(stock_id)
                stock_context = f"\n\n## 股票 {stock_id} 的最新數據\n{stock_data}"
                sources.append("FinMind 股票數據")
                sources.append("證交所三大法人買賣超")
            except Exception as e:
                stock_context = f"\n\n（無法取得股票 {stock_id} 的數據：{str(e)}）"

        # 組合用戶訊息
        full_message = f"{self.SYSTEM_PROMPT}\n\n{user_message}{stock_context}"

        # 呼叫 Gemini API
        chat = self.llm.start_chat(history=history)
        response = chat.send_message(
            full_message,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1000,
            )
        )

        ai_response = response.text

        # 提取相關股票代碼
        related_stocks = self._extract_stock_ids(ai_response)
        if stock_id and stock_id not in related_stocks:
            related_stocks.insert(0, stock_id)

        return {"response": ai_response, "related_stocks": related_stocks, "sources": sources}

    def _get_stock_context(self, stock_id: str) -> str:
        """取得股票即時數據作為上下文"""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        start_str = start_date.strftime("%Y-%m-%d")

        # 取得價格
        prices = self.finmind.get_stock_price(stock_id, start_str)
        latest = prices.iloc[-1] if len(prices) > 0 else None

        # 取得籌碼
        institutions = self.finmind.get_institutional_investors(stock_id, start_str)

        foreign_buy = institutions.tail(5)["Foreign_Investor_buy"].sum() if len(institutions) >= 5 else 0
        foreign_sell = institutions.tail(5)["Foreign_Investor_sell"].sum() if len(institutions) >= 5 else 0
        trust_buy = institutions.tail(5)["Investment_Trust_buy"].sum() if len(institutions) >= 5 else 0
        trust_sell = institutions.tail(5)["Investment_Trust_sell"].sum() if len(institutions) >= 5 else 0

        context = f"""
- 最新收盤價：{latest['close'] if latest is not None else 'N/A'}
- 成交量：{latest['Trading_Volume'] if latest is not None else 'N/A'}
- 近5日外資買賣超：{foreign_buy - foreign_sell if len(institutions) >= 5 else 'N/A'}
- 近5日投信買賣超：{trust_buy - trust_sell if len(institutions) >= 5 else 'N/A'}
"""
        return context

    def _extract_stock_ids(self, text: str) -> List[str]:
        """從文字中提取股票代碼"""
        import re

        # 匹配 4 位數字的股票代碼
        pattern = r"\b(\d{4})\b"
        matches = re.findall(pattern, text)
        # 過濾可能不是股票代碼的數字（如年份）
        valid_ids = [m for m in matches if 1000 <= int(m) <= 9999 and int(m) not in range(1900, 2100)]
        return list(set(valid_ids))[:5]  # 最多返回5個
