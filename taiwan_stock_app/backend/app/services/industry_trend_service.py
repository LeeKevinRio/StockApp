"""
Industry Trend Analysis Service - 產業趨勢分析
支援備援機制: Gemini -> Groq -> 簡單數據分析
"""
from typing import Dict, List, Optional
from datetime import date, timedelta
import google.generativeai as genai
import json
import logging

from app.data_fetchers import FinMindFetcher
from app.config import settings
from app.database import SessionLocal
from app.models import Stock
from app.services.ai_suggestion_service import get_groq_client

logger = logging.getLogger(__name__)


class IndustryTrendService:
    """產業趨勢分析服務"""

    def __init__(self):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self.llm = genai.GenerativeModel(settings.AI_MODEL)

    def get_all_industries(self) -> List[str]:
        """取得所有產業類別"""
        db = SessionLocal()
        try:
            industries = db.query(Stock.industry).distinct().all()
            return [i[0] for i in industries if i[0] and i[0] != '其他' and len(i[0]) > 1]
        finally:
            db.close()

    def get_industry_stocks(self, industry: str) -> List[Dict]:
        """取得特定產業的股票列表"""
        db = SessionLocal()
        try:
            stocks = db.query(Stock).filter(Stock.industry == industry).limit(20).all()
            return [{"stock_id": s.stock_id, "name": s.name} for s in stocks]
        finally:
            db.close()

    def collect_industry_data(self, industry: str, days: int = 20) -> Optional[Dict]:
        """收集產業數據"""
        stocks = self.get_industry_stocks(industry)
        if not stocks:
            return None

        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        # 取樣代表性股票分析
        sample_stocks = stocks[:min(5, len(stocks))]

        industry_data = {
            "industry": industry,
            "stock_count": len(stocks),
            "sample_stocks": [],
            "avg_change_5d": 0,
            "avg_change_20d": 0,
            "foreign_net_buy": 0,
            "trust_net_buy": 0,
        }

        total_change_5d = 0
        total_change_20d = 0
        total_foreign = 0
        total_trust = 0
        valid_count = 0

        for stock in sample_stocks:
            try:
                prices = self.finmind.get_stock_price(
                    stock["stock_id"], start_str, end_str
                )
                if prices is None or len(prices) < 5:
                    continue

                # 計算漲跌幅
                current = float(prices.iloc[-1]["close"])
                price_5d_ago = float(prices.iloc[-6]["close"]) if len(prices) >= 6 else current
                price_20d_ago = float(prices.iloc[0]["close"])

                change_5d = (current - price_5d_ago) / price_5d_ago * 100 if price_5d_ago > 0 else 0
                change_20d = (current - price_20d_ago) / price_20d_ago * 100 if price_20d_ago > 0 else 0

                # 取得法人數據
                foreign_net = 0
                trust_net = 0
                try:
                    institutions = self.finmind.get_institutional_investors(
                        stock["stock_id"], start_str, end_str
                    )
                    if institutions is not None and len(institutions) > 0:
                        # 計算外資淨買超
                        if 'Foreign_Investor' in institutions.columns:
                            foreign_net = institutions['Foreign_Investor'].sum() / 1000
                        # 計算投信淨買超
                        if 'Investment_Trust' in institutions.columns:
                            trust_net = institutions['Investment_Trust'].sum() / 1000
                except Exception:
                    pass

                industry_data["sample_stocks"].append({
                    "stock_id": stock["stock_id"],
                    "name": stock["name"],
                    "current_price": round(current, 2),
                    "change_5d": round(change_5d, 2),
                    "change_20d": round(change_20d, 2),
                })

                total_change_5d += change_5d
                total_change_20d += change_20d
                total_foreign += foreign_net
                total_trust += trust_net
                valid_count += 1

            except Exception as e:
                logger.error("處理 %s 時發生錯誤: %s", stock['stock_id'], e)
                continue

        if valid_count > 0:
            industry_data["avg_change_5d"] = round(total_change_5d / valid_count, 2)
            industry_data["avg_change_20d"] = round(total_change_20d / valid_count, 2)
            industry_data["foreign_net_buy"] = int(total_foreign)
            industry_data["trust_net_buy"] = int(total_trust)
            return industry_data

        return None

    def analyze_industries(self, limit: int = 15) -> Dict:
        """分析主要產業趨勢"""
        industries = self.get_all_industries()

        # 收集產業數據
        industry_summaries = []
        for industry in industries[:limit]:
            try:
                data = self.collect_industry_data(industry, days=20)
                if data and data.get("sample_stocks"):
                    industry_summaries.append(data)
            except Exception as e:
                logger.error("分析產業 %s 時發生錯誤: %s", industry, e)
                continue

        return {
            "industries": industry_summaries,
            "analysis_date": date.today().isoformat(),
        }

    def generate_trend_analysis(self) -> Dict:
        """生成 AI 產業趨勢分析"""
        # 收集產業數據
        data = self.analyze_industries(limit=15)

        if not data.get("industries"):
            return {"error": "無法取得產業數據"}

        # 組合 Prompt
        system_prompt = """你是一位專業的台股產業分析師，擅長分析產業趨勢和投資機會。

請根據提供的產業數據，分析台股各產業的未來趨勢，並回傳 JSON 格式的分析結果：

{
  "analysis_date": "YYYY-MM-DD",
  "market_overview": "整體市場概況（100-150字）",
  "bullish_industries": [
    {
      "industry": "產業名稱",
      "probability": 0.0-1.0（上漲機率）,
      "reasoning": "上漲原因（80-120字）",
      "key_factors": ["因素1", "因素2", "因素3"],
      "representative_stocks": ["股票代碼1", "股票代碼2"],
      "risk_factors": ["風險1", "風險2"]
    }
  ],
  "bearish_industries": [
    {
      "industry": "產業名稱",
      "probability": 0.0-1.0（下跌機率）,
      "reasoning": "下跌原因（80-120字）",
      "key_factors": ["因素1", "因素2", "因素3"],
      "representative_stocks": ["股票代碼1", "股票代碼2"],
      "avoid_reasons": ["避開理由1", "避開理由2"]
    }
  ],
  "neutral_industries": [
    {
      "industry": "產業名稱",
      "reasoning": "持平原因（50-80字）"
    }
  ],
  "investment_suggestions": "整體投資建議（100-150字）",
  "disclaimer": "投資警語"
}

分析重點：
1. 根據近期漲跌幅判斷趨勢強弱
2. 外資和投信的買賣超是重要訊號
3. 結合你對台灣產業和國際趨勢的了解
4. 考慮季節性因素和政策影響
5. bullish_industries 應列出 3-5 個看漲產業
6. bearish_industries 應列出 2-3 個看跌產業
7. probability 應基於數據合理評估

請只回傳 JSON 格式，不要包含其他文字。"""

        user_prompt = f"""請分析以下台股產業數據，預測未來趨勢：

## 分析日期
{data['analysis_date']}

## 產業數據
{json.dumps(data['industries'], ensure_ascii=False, indent=2)}

請根據以上數據，結合你對全球經濟和台灣產業的了解，分析：
1. 哪些產業近期可能上漲？為什麼？
2. 哪些產業近期可能下跌？為什麼？
3. 投資人應該如何配置？

請回傳完整的 JSON 分析結果。"""

        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # 1. 嘗試 Gemini
        result = self._call_gemini(full_prompt)
        if result is not None:
            return result

        # 2. Gemini 失敗，嘗試 Groq
        logger.warning("Gemini industry analysis failed, trying Groq...")
        result = self._call_groq(full_prompt)
        if result is not None:
            return result

        # 3. 全部失敗，返回基於數據的簡單分析
        logger.warning("All AI providers failed for industry analysis, using simple analysis")
        return self._generate_simple_analysis(data)

    def _call_gemini(self, prompt: str) -> Optional[Dict]:
        """呼叫 Gemini API"""
        try:
            response = self.llm.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    response_mime_type="application/json",
                )
            )
            return json.loads(response.text)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                logger.warning("Gemini quota exceeded (industry): %s", e)
            else:
                logger.error("Gemini industry analysis error: %s", e)
            return None

    def _call_groq(self, prompt: str) -> Optional[Dict]:
        """呼叫 Groq API"""
        groq_client = get_groq_client()
        if groq_client is None:
            logger.warning("Groq client not available for industry analysis")
            return None

        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "你是一位專業的台股產業分析師，必須以 JSON 格式回覆。"},
                    {"role": "user", "content": prompt}
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
                logger.warning("Groq rate limit exceeded (industry): %s", e)
            else:
                logger.error("Groq industry analysis error: %s", e)
            return None

    def _generate_simple_analysis(self, data: Dict) -> Dict:
        """當 AI 分析失敗時，生成簡單的數據分析"""
        industries = data.get("industries", [])

        # 按漲跌幅排序
        sorted_industries = sorted(industries, key=lambda x: x.get("avg_change_5d", 0), reverse=True)

        bullish = []
        bearish = []
        neutral = []

        for ind in sorted_industries:
            change = ind.get("avg_change_5d", 0)
            if change > 2:
                bullish.append({
                    "industry": ind["industry"],
                    "probability": min(0.5 + change / 20, 0.85),
                    "reasoning": f"近5日平均漲幅 {change}%，顯示強勢走勢。",
                    "key_factors": ["短期動能強勁", "資金持續流入"],
                    "representative_stocks": [s["stock_id"] for s in ind.get("sample_stocks", [])[:2]],
                    "risk_factors": ["短線漲多回檔風險"]
                })
            elif change < -2:
                bearish.append({
                    "industry": ind["industry"],
                    "probability": min(0.5 + abs(change) / 20, 0.85),
                    "reasoning": f"近5日平均跌幅 {abs(change)}%，顯示弱勢走勢。",
                    "key_factors": ["短期動能疲弱", "資金流出明顯"],
                    "representative_stocks": [s["stock_id"] for s in ind.get("sample_stocks", [])[:2]],
                    "avoid_reasons": ["趨勢向下", "缺乏買盤支撐"]
                })
            else:
                neutral.append({
                    "industry": ind["industry"],
                    "reasoning": f"近期走勢平穩，漲跌幅 {change}%。"
                })

        return {
            "analysis_date": data.get("analysis_date", date.today().isoformat()),
            "market_overview": "根據近期產業數據分析，市場呈現分化走勢，建議投資人關注強勢產業並避開弱勢族群。",
            "bullish_industries": bullish[:5],
            "bearish_industries": bearish[:3],
            "neutral_industries": neutral[:3],
            "investment_suggestions": "建議採取選股不選市策略，重點布局表現強勢的產業，同時控制整體倉位風險。",
            "disclaimer": "本分析僅供參考，不構成投資建議。投資有風險，請自行評估。"
        }
