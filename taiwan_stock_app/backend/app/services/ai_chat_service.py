"""
AI Chat Service - AI 問答服務
支援備援機制: Gemini -> Groq -> 錯誤提示
"""
from typing import List, Dict, Optional
from datetime import date, timedelta
import logging
import google.generativeai as genai

from app.data_fetchers import FinMindFetcher
from app.config import settings
from app.services.ai_suggestion_service import get_groq_client

logger = logging.getLogger(__name__)


class AIChatService:
    """AI 問答服務"""

    SYSTEM_PROMPT_TEMPLATE = """你是一位專業的台股投資顧問 AI 助手。

## 今天日期：{today}

你可以：
1. 回答關於台股投資的各種問題
2. 分析特定股票的技術面、籌碼面、基本面
3. 解釋投資概念和術語
4. 提供市場趨勢分析

重要原則：
- 所有投資建議僅供參考，不構成投資決策依據
- 回答時引用具體數據，說明數據來源
- 保持客觀中立，提醒投資風險
- 如果不確定或沒有相關數據，誠實告知
- **你的訓練資料有截止日期，若用戶詢問的內容超出你的知識範圍，請誠實說明你的資料截止時間，並根據下方提供的即時數據回答**
- **絕對不要編造或猜測你不知道的股價、財報數據，若無即時數據，請明確告知**

當用戶詢問特定股票時，你會收到該股票的最新數據，請根據數據提供分析。"""

    # 產業關鍵字 → 代表性個股（用於自動補充即時數據）
    INDUSTRY_STOCKS = {
        "半導體": ["2330", "2303", "2454", "3711", "2379"],
        "晶圓代工": ["2330", "6770"],
        "IC設計": ["2454", "3711", "2379", "3034"],
        "封測": ["2311", "3711", "2325"],
        "面板": ["2409", "3481", "6116"],
        "電子": ["2317", "2382", "2308", "3231"],
        "金融": ["2881", "2882", "2884", "2886", "2891"],
        "銀行": ["2881", "2882", "2884", "2886"],
        "保險": ["2823", "2816", "2832"],
        "證券": ["6005", "2855", "6021"],
        "鋼鐵": ["2002", "2006", "2014"],
        "航運": ["2603", "2609", "2615"],
        "貨櫃": ["2603", "2609", "2615"],
        "散裝": ["2605", "2606", "2634"],
        "航空": ["2610", "2618", "6288"],
        "汽車": ["2201", "2207", "2227"],
        "電動車": ["2201", "3037", "2308", "6274"],
        "食品": ["1216", "1301", "2912"],
        "營建": ["2501", "2504", "2542", "5534"],
        "生技": ["4743", "6446", "1760", "4147"],
        "觀光": ["2702", "2706", "2707"],
        "電信": ["2412", "3045", "4904"],
        "石化": ["1301", "1303", "1326", "6505"],
        "塑膠": ["1301", "1303", "1326"],
        "紡織": ["1402", "1434", "1476"],
        "光電": ["2349", "3008", "6285"],
        "AI": ["2330", "2454", "3443", "2382", "3231"],
        "人工智慧": ["2330", "2454", "3443", "2382", "3231"],
        "5G": ["2454", "3045", "4904", "2382"],
        "綠能": ["6244", "3576", "6443"],
        "太陽能": ["3576", "6244", "6443"],
        "風電": ["2208", "2634"],
        "PCB": ["3037", "8046", "2353"],
        "伺服器": ["2382", "3231", "2395", "4938"],
        "記憶體": ["2303", "8299", "3006"],
        "DRAM": ["2303", "8299"],
        "被動元件": ["2327", "3533"],
        "連接器": ["2354", "3023"],
        "ABF載板": ["3037", "8046", "2353"],
        "散熱": ["3092", "6230", "3548"],
        "ETF": ["0050", "0056", "00878", "00919"],
    }

    def __init__(self, subscription_tier: str = 'free', ai_client=None):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        genai.configure(api_key=settings.GOOGLE_API_KEY)

        # Select model based on subscription tier
        if subscription_tier == 'pro':
            self.model = settings.AI_MODEL_PRO
        else:
            self.model = settings.AI_MODEL_FREE

        self.llm = genai.GenerativeModel(self.model)
        self.subscription_tier = subscription_tier
        # BYOK: 用戶自訂 AI client（若有）
        self.ai_client = ai_client

    def _get_system_prompt(self) -> str:
        """生成包含今日日期的系統提示詞"""
        return self.SYSTEM_PROMPT_TEMPLATE.format(today=date.today().strftime("%Y-%m-%d"))

    def _detect_industry_stocks(self, message: str) -> List[str]:
        """從用戶訊息中偵測產業關鍵字，回傳代表性個股列表"""
        matched_stocks = []
        for keyword, stocks in self.INDUSTRY_STOCKS.items():
            if keyword in message:
                matched_stocks.extend(stocks)
        # 去重，最多取 5 檔
        seen = set()
        unique = []
        for s in matched_stocks:
            if s not in seen:
                seen.add(s)
                unique.append(s)
        return unique[:5]

    @classmethod
    def for_user(cls, user, db=None) -> 'AIChatService':
        """
        工廠方法：根據用戶訂閱級別創建服務實例，支援 BYOK
        """
        from app.services.ai_client_factory import AIClientFactory

        tier = getattr(user, 'subscription_tier', 'free') or 'free'
        ai_client = None
        if db is not None:
            config = AIClientFactory.resolve_config(user, db)
            if config:
                ai_client = AIClientFactory.create_client(config)
        return cls(subscription_tier=tier, ai_client=ai_client)

    def chat(
        self,
        user_message: str,
        stock_id: Optional[str] = None,
        chat_history: Optional[List[Dict]] = None,
    ) -> Dict:
        """處理用戶問答，支援 Gemini -> Groq fallback"""
        system_prompt = self._get_system_prompt()

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
                stock_context = f"\n\n## 股票 {stock_id} 的最新即時數據（{date.today()}）\n{stock_data}"
                sources.append("FinMind 股票數據")
                sources.append("證交所三大法人買賣超")
            except Exception as e:
                stock_context = f"\n\n（無法取得股票 {stock_id} 的數據：{str(e)}）"

        # 如果沒有指定股票，偵測產業關鍵字並補充即時數據
        if not stock_id:
            industry_stocks = self._detect_industry_stocks(user_message)
            if industry_stocks:
                industry_context_parts = []
                for sid in industry_stocks:
                    try:
                        data = self._get_stock_context(sid)
                        industry_context_parts.append(f"### {sid}\n{data}")
                    except Exception:
                        pass
                if industry_context_parts:
                    stock_context = f"\n\n## 相關產業個股即時數據（{date.today()}）\n" + "\n".join(industry_context_parts)
                    sources.append("FinMind 股票數據")
                    sources.append("證交所三大法人買賣超")

        # 組合用戶訊息
        full_message = f"{system_prompt}\n\n{user_message}{stock_context}"

        ai_response = None

        # 0. 若有 BYOK 自訂 client，優先使用
        if self.ai_client is not None:
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                ]
                if chat_history:
                    for msg in chat_history[-10:]:
                        messages.append({"role": msg["role"], "content": msg["content"]})
                messages.append({"role": "user", "content": f"{user_message}{stock_context}"})
                ai_response = self.ai_client.chat(messages)
            except Exception as e:
                logger.warning(f"BYOK chat client failed: {e}, falling back to system default")

        # 1. 嘗試 Gemini
        if ai_response is None:
            ai_response = self._call_gemini_chat(full_message, history)

        # 2. Gemini 失敗，嘗試 Groq
        if ai_response is None:
            logger.warning("Gemini chat failed, trying Groq...")
            ai_response = self._call_groq_chat(full_message, chat_history, system_prompt)

        # 3. 全部失敗
        if ai_response is None:
            raise Exception("AI 服務暫時不可用（Gemini 與 Groq 皆無法回應），請稍後再試。")

        # 提取相關股票代碼
        related_stocks = self._extract_stock_ids(ai_response)
        if stock_id and stock_id not in related_stocks:
            related_stocks.insert(0, stock_id)

        return {"response": ai_response, "related_stocks": related_stocks, "sources": sources}

    def _call_gemini_chat(self, message: str, history: List[Dict]) -> Optional[str]:
        """呼叫 Gemini Chat API"""
        try:
            chat = self.llm.start_chat(history=history)
            response = chat.send_message(
                message,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=4096,
                )
            )
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower() or "ResourceExhausted" in error_str:
                logger.warning(f"Gemini chat quota exceeded: {e}")
            else:
                logger.error(f"Gemini chat error: {e}")
            return None

    def _call_groq_chat(self, message: str, chat_history: Optional[List[Dict]] = None, system_prompt: Optional[str] = None) -> Optional[str]:
        """呼叫 Groq Chat API"""
        groq_client = get_groq_client()
        if groq_client is None:
            logger.warning("Groq client not available (API key not set or package not installed)")
            return None

        prompt = system_prompt or self._get_system_prompt()
        try:
            messages = [
                {"role": "system", "content": prompt}
            ]
            # 加入對話歷史
            if chat_history:
                for msg in chat_history[-10:]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            # 加入當前訊息（去掉 system prompt 前綴，因為已放在 system message）
            user_content = message.replace(prompt + "\n\n", "")
            messages.append({"role": "user", "content": user_content})

            chat_completion = groq_client.chat.completions.create(
                messages=messages,
                model=settings.GROQ_MODEL,
                temperature=0.7,
                max_tokens=4096,
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate" in error_str.lower():
                logger.warning(f"Groq chat rate limit exceeded: {e}")
            else:
                logger.error(f"Groq chat error: {e}")
            return None

    def _get_stock_context(self, stock_id: str) -> str:
        """取得股票即時數據作為上下文"""
        end_date = date.today()
        start_date = end_date - timedelta(days=30)
        start_str = start_date.strftime("%Y-%m-%d")

        # 取得價格
        prices = self.finmind.get_stock_price(stock_id, start_str)
        latest = prices.iloc[-1] if len(prices) > 0 else None
        latest_date = latest['date'] if latest is not None and 'date' in latest else end_date.strftime("%Y-%m-%d")

        # 計算近期漲跌幅
        price_change_5d = ""
        price_change_20d = ""
        if latest is not None and len(prices) >= 5:
            close_now = float(latest['close'])
            close_5d = float(prices.iloc[-5]['close'])
            price_change_5d = f"{((close_now - close_5d) / close_5d * 100):.2f}%"
        if latest is not None and len(prices) >= 20:
            close_now = float(latest['close'])
            close_20d = float(prices.iloc[-20]['close'])
            price_change_20d = f"{((close_now - close_20d) / close_20d * 100):.2f}%"

        # 取得籌碼
        institutions = self.finmind.get_institutional_investors(stock_id, start_str)

        foreign_buy = institutions.tail(5)["Foreign_Investor_buy"].sum() if len(institutions) >= 5 else 0
        foreign_sell = institutions.tail(5)["Foreign_Investor_sell"].sum() if len(institutions) >= 5 else 0
        trust_buy = institutions.tail(5)["Investment_Trust_buy"].sum() if len(institutions) >= 5 else 0
        trust_sell = institutions.tail(5)["Investment_Trust_sell"].sum() if len(institutions) >= 5 else 0

        context = f"""
- 資料日期：{latest_date}
- 最新收盤價：{latest['close'] if latest is not None else 'N/A'}
- 成交量：{latest['Trading_Volume'] if latest is not None else 'N/A'}
- 近5日漲跌幅：{price_change_5d or 'N/A'}
- 近20日漲跌幅：{price_change_20d or 'N/A'}
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
