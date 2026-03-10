"""
AI Stock Discovery Service - 潛力股掃描
掃描市場上未在自選股中的股票，利用 AI 分析找出短期（5天）高機率上漲的潛力股
支援台股(TW)與美股(US)
"""
from typing import Dict, List, Optional
from datetime import date, timedelta
from google import genai
from google.genai import types as genai_types
import json
import time
import logging
import traceback
import pandas as pd

from app.data_fetchers import FinMindFetcher, USStockFetcher
from app.config import settings
from app.services.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

# 掃描候選股票池
TW_CANDIDATE_STOCKS = {
    "半導體": ["2330", "2303", "2454", "2408", "3034", "6770", "3443", "5274", "2449", "3529"],
    "AI伺服器": ["2382", "3231", "6669", "2324", "3017", "2356", "3036"],
    "電子": ["2317", "2308", "2357", "2395", "3711", "2327", "2345", "3037", "3044"],
    "PCB/IC載板": ["3037", "8046", "3189", "2368", "6153"],
    "記憶體": ["2344", "3481", "8299", "3006"],
    "金融": ["2882", "2881", "2886", "2891", "2892", "2884", "2880", "5880"],
    "傳產": ["2002", "1301", "1303", "1326", "1101", "1216"],
    "航運": ["2603", "2609", "2615", "2618"],
    "通信": ["2412", "4904", "3045"],
    "生技": ["6446", "4743", "6472", "4726", "1795"],
    "綠能": ["3576", "6244", "3691"],
    "ETF": ["00631L", "0050", "0056", "00878", "00919"],
}

US_CANDIDATE_STOCKS = {
    "科技巨頭": ["AAPL", "GOOGL", "MSFT", "AMZN", "META"],
    "AI/半導體": ["NVDA", "AMD", "AVGO", "TSM", "QCOM", "MRVL", "ARM", "SMCI"],
    "軟體/雲端": ["CRM", "SNOW", "PLTR", "NOW", "PANW", "CRWD", "NET"],
    "電商/消費": ["TSLA", "NFLX", "UBER", "ABNB", "SHOP", "DASH"],
    "金融": ["JPM", "GS", "V", "MA", "AXP"],
    "醫療": ["LLY", "UNH", "ABBV", "MRK", "ISRG"],
    "能源": ["XOM", "CVX", "COP"],
    "新興成長": ["COIN", "RBLX", "HOOD", "SOFI", "DKNG", "ROKU"],
}


# 股票名稱對照表（避免每次查 API）
STOCK_NAMES = {
    # 台股
    "2330": "台積電", "2303": "聯電", "2454": "聯發科", "2408": "南亞科",
    "3034": "聯詠", "6770": "力積電", "3443": "創意", "5274": "信驊",
    "2449": "京元電子", "3529": "力旺", "2382": "廣達", "3231": "緯創",
    "6669": "緯穎", "2324": "仁寶", "3017": "奇鋐", "2356": "英業達",
    "3036": "文曄", "2317": "鴻海", "2308": "台達電", "2357": "華碩",
    "2395": "研華", "3711": "日月光", "2327": "國巨", "2345": "智邦",
    "3037": "欣興", "3044": "健鼎", "8046": "南電", "3189": "景碩",
    "2368": "金像電", "6153": "嘉聯益", "2344": "華邦電", "3481": "群創",
    "8299": "群聯", "3006": "晶豪科", "2882": "國泰金", "2881": "富邦金",
    "2886": "兆豐金", "2891": "中信金", "2892": "第一金", "2884": "玉山金",
    "2880": "華南金", "5880": "合庫金", "2002": "中鋼", "1301": "台塑",
    "1303": "南亞", "1326": "台化", "1101": "台泥", "1216": "統一",
    "2603": "長榮", "2609": "陽明", "2615": "萬海", "2618": "長榮航",
    "2412": "中華電", "4904": "遠傳", "3045": "台灣大",
    "6446": "藥華藥", "4743": "合一", "6472": "保瑞", "4726": "永昕",
    "1795": "美時", "3576": "聯合再生", "6244": "茂迪", "3691": "碩禾",
    "00631L": "元大台灣50正2", "0050": "元大台灣50", "0056": "元大高股息",
    "00878": "國泰永續高股息", "00919": "群益台灣精選高息",
    # 美股
    "AAPL": "Apple", "GOOGL": "Alphabet", "MSFT": "Microsoft",
    "AMZN": "Amazon", "META": "Meta", "NVDA": "NVIDIA", "AMD": "AMD",
    "AVGO": "Broadcom", "TSM": "台積電ADR", "QCOM": "Qualcomm",
    "MRVL": "Marvell", "ARM": "ARM Holdings", "SMCI": "Super Micro",
    "CRM": "Salesforce", "SNOW": "Snowflake", "PLTR": "Palantir",
    "NOW": "ServiceNow", "PANW": "Palo Alto", "CRWD": "CrowdStrike",
    "NET": "Cloudflare", "TSLA": "Tesla", "NFLX": "Netflix",
    "UBER": "Uber", "ABNB": "Airbnb", "SHOP": "Shopify", "DASH": "DoorDash",
    "JPM": "JPMorgan", "GS": "Goldman Sachs", "V": "Visa", "MA": "Mastercard",
    "AXP": "American Express", "LLY": "Eli Lilly", "UNH": "UnitedHealth",
    "ABBV": "AbbVie", "MRK": "Merck", "ISRG": "Intuitive Surgical",
    "XOM": "ExxonMobil", "CVX": "Chevron", "COP": "ConocoPhillips",
    "COIN": "Coinbase", "RBLX": "Roblox", "HOOD": "Robinhood",
    "SOFI": "SoFi", "DKNG": "DraftKings", "ROKU": "Roku",
}


class AIDiscoveryService:
    """AI 潛力股掃描服務"""

    def __init__(self, subscription_tier: str = "free"):
        self.finmind = FinMindFetcher(settings.FINMIND_TOKEN)
        self.us_fetcher = USStockFetcher()

        if subscription_tier == "pro":
            self.model = settings.AI_MODEL_PRO
        else:
            self.model = settings.AI_MODEL_FREE

        self.gemini_client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        self.subscription_tier = subscription_tier

    # ------------------------------------------------------------------
    # 公開方法
    # ------------------------------------------------------------------
    def discover_stocks(self, market: str = "TW", top_n: int = 5) -> Dict:
        """
        掃描市場找出高機率短期上漲的潛力股

        Returns:
            {
                "market": "TW",
                "scan_date": "2026-03-10",
                "analysis_period": "5 days",
                "picks": [ ... ],
                "market_summary": "..."
            }
        """
        candidates = TW_CANDIDATE_STOCKS if market == "TW" else US_CANDIDATE_STOCKS
        all_symbols = []
        for symbols in candidates.values():
            all_symbols.extend(symbols)
        # 去重
        all_symbols = list(dict.fromkeys(all_symbols))

        logger.info(f"[Discovery] Scanning {len(all_symbols)} {market} stocks...")

        # 第 1 步: 快速技術面篩選，縮小範圍
        screened = self._quick_screen(all_symbols, market)
        logger.info(f"[Discovery] Quick screen passed: {len(screened)} stocks")

        if not screened:
            return {
                "market": market,
                "scan_date": date.today().isoformat(),
                "analysis_period": "5 trading days",
                "picks": [],
                "market_summary": "目前市場無明顯短期上漲訊號的股票",
            }

        # 第 2 步: 用 AI 深度分析篩選出的候選股
        picks = self._ai_rank(screened, market, top_n)

        return {
            "market": market,
            "scan_date": date.today().isoformat(),
            "analysis_period": "5 trading days",
            "picks": picks,
            "market_summary": self._generate_market_summary(picks, market),
        }

    # ------------------------------------------------------------------
    # 第 1 步: 快速技術面篩選
    # ------------------------------------------------------------------
    def _quick_screen(self, symbols: List[str], market: str) -> List[Dict]:
        """用技術指標快速篩選出有上漲潛力的股票"""
        passed = []

        for symbol in symbols:
            try:
                data = self._get_price_data(symbol, market, days=60)
                if data is None or len(data) < 30:
                    continue

                df = pd.DataFrame(data)
                df["close"] = df["close"].astype(float)
                df["open"] = df["open"].astype(float)
                df["high"] = df["high"].astype(float)
                df["low"] = df["low"].astype(float)
                df["volume"] = df.get("Trading_Volume", df.get("volume", pd.Series([0] * len(df)))).astype(int)

                indicators = TechnicalIndicators.get_latest_indicators(df)
                if not indicators:
                    continue

                close = df["close"].iloc[-1]
                score = self._compute_bullish_score(close, indicators, df)

                if score >= 40:
                    # 計算近 5 日漲跌幅
                    change_5d = 0
                    if len(df) >= 6:
                        change_5d = round((close / float(df["close"].iloc[-6]) - 1) * 100, 2)
                    # 計算近 20 日漲跌幅
                    change_20d = 0
                    if len(df) >= 21:
                        change_20d = round((close / float(df["close"].iloc[-21]) - 1) * 100, 2)

                    passed.append({
                        "symbol": symbol,
                        "close": round(close, 2),
                        "score": score,
                        "change_5d": change_5d,
                        "change_20d": change_20d,
                        "rsi": round(indicators.get("rsi", 50), 1),
                        "macd_status": "bullish" if indicators.get("macd", 0) > indicators.get("macd_signal", 0) else "bearish",
                        "ma_trend": self._get_ma_trend(close, indicators),
                        "volume_ratio": self._volume_ratio(df),
                        "indicators": indicators,
                    })

                # 避免 API 過載
                time.sleep(0.1)

            except Exception as e:
                logger.debug(f"[Discovery] Skip {symbol}: {e}")
                continue

        # 依分數排序
        passed.sort(key=lambda x: x["score"], reverse=True)
        # 最多取前 15 支進入 AI 分析
        return passed[:15]

    def _compute_bullish_score(self, close: float, ind: Dict, df: pd.DataFrame) -> int:
        """計算看漲分數 (0-100)"""
        score = 50  # 基準分

        # RSI 超賣反彈 (+15)
        rsi = ind.get("rsi", 50)
        if rsi <= 30:
            score += 15
        elif rsi <= 40:
            score += 10
        elif rsi >= 70:
            score -= 10
        elif rsi >= 80:
            score -= 20

        # MACD 金叉 (+10)
        macd = ind.get("macd", 0)
        macd_signal = ind.get("macd_signal", 0)
        if macd > macd_signal:
            score += 10
            if ind.get("macd_histogram", macd - macd_signal) > 0:
                score += 5

        # KD 超賣 / 金叉 (+10)
        k = ind.get("k", 50)
        d = ind.get("d", 50)
        if k < 20 and d < 20:
            score += 10
        elif k > d and k < 50:
            score += 5

        # 均線多頭排列 (+10)
        ma5 = ind.get("ma5", 0)
        ma10 = ind.get("ma10", 0)
        ma20 = ind.get("ma20", 0)
        if ma5 and ma10 and ma20:
            if ma5 > ma10 > ma20:
                score += 10
            elif close > ma5 > ma10:
                score += 5
            elif close < ma5 < ma10 < ma20:
                score -= 10

        # 股價站上均線 (+5)
        if ma20 and close > ma20:
            score += 5
        elif ma20 and close < ma20:
            score -= 5

        # 布林通道下軌附近 (+10)
        bb_lower = ind.get("bb_lower", 0)
        bb_upper = ind.get("bb_upper", 0)
        if bb_lower and bb_upper and bb_lower > 0:
            bb_position = (close - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5
            if bb_position < 0.2:
                score += 10
            elif bb_position < 0.4:
                score += 5

        # 成交量放大 (+5)
        vol_ratio = self._volume_ratio(df)
        if vol_ratio > 1.5:
            score += 5
        elif vol_ratio > 2.0:
            score += 10

        return max(0, min(100, score))

    def _volume_ratio(self, df: pd.DataFrame) -> float:
        """計算近 5 日成交量 vs 20 日均量比"""
        try:
            vol_col = "Trading_Volume" if "Trading_Volume" in df.columns else "volume"
            vols = df[vol_col].astype(float)
            if len(vols) < 20:
                return 1.0
            avg_5 = vols.iloc[-5:].mean()
            avg_20 = vols.iloc[-20:].mean()
            return round(avg_5 / avg_20, 2) if avg_20 > 0 else 1.0
        except Exception:
            return 1.0

    def _get_ma_trend(self, close: float, ind: Dict) -> str:
        ma5 = ind.get("ma5", 0)
        ma10 = ind.get("ma10", 0)
        ma20 = ind.get("ma20", 0)
        if ma5 and ma10 and ma20:
            if ma5 > ma10 > ma20:
                return "bullish"
            elif ma5 < ma10 < ma20:
                return "bearish"
        return "neutral"

    def _get_price_data(self, symbol: str, market: str, days: int = 60):
        """取得價格數據"""
        if market == "US":
            data = self.us_fetcher.get_stock_price(symbol, period=f"{days}d")
            if data:
                df = pd.DataFrame(data)
                return df
            return None
        else:
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            try:
                df = self.finmind.get_stock_price(
                    symbol, start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
                )
                if len(df) > 0:
                    if "max" in df.columns:
                        df["high"] = df["max"]
                    if "min" in df.columns:
                        df["low"] = df["min"]
                    return df
            except Exception:
                pass
            return None

    # ------------------------------------------------------------------
    # 第 2 步: AI 深度分析
    # ------------------------------------------------------------------
    def _ai_rank(self, candidates: List[Dict], market: str, top_n: int) -> List[Dict]:
        """用 AI 從候選股中挑出最具上漲潛力的 top_n 支"""

        # 準備候選股摘要
        stock_summaries = []
        for c in candidates:
            stock_summaries.append(
                f"- {c['symbol']}: 收盤價={c['close']}, "
                f"5日漲跌={c['change_5d']}%, 20日漲跌={c['change_20d']}%, "
                f"RSI={c['rsi']}, MACD={c['macd_status']}, "
                f"均線趨勢={c['ma_trend']}, 量比={c['volume_ratio']}, "
                f"技術分數={c['score']}"
            )

        currency = "TWD" if market == "TW" else "USD"
        market_name = "台股" if market == "TW" else "美股"

        prompt = f"""你是一位專業的短線交易分析師。請從以下 {market_name} 候選股票中，挑選出最有可能在未來 5 個交易日上漲的前 {top_n} 支股票。

## 候選股票技術指標摘要
{chr(10).join(stock_summaries)}

## 分析要求
1. 綜合考量技術指標（RSI 超賣反彈、MACD 金叉、均線支撐、量價配合）
2. 評估短期上漲機率（5 個交易日）
3. 給出具體的預測漲幅區間
4. 說明推薦理由（限 50 字以內）
5. 設定停損價位

## 輸出格式
請嚴格按照以下 JSON 格式回覆，不要加任何其他文字：
{{
  "picks": [
    {{
      "symbol": "股票代碼",
      "name": "公司名稱",
      "current_price": 收盤價數字,
      "predicted_change_pct": 預測5日漲幅百分比數字,
      "probability": 上漲機率(0.5-0.95),
      "target_price": 目標價數字,
      "stop_loss_price": 停損價數字,
      "risk_level": "LOW/MEDIUM/HIGH",
      "reasoning": "推薦理由（50字以內）",
      "key_signals": ["訊號1", "訊號2", "訊號3"]
    }}
  ]
}}

注意：
- probability 應在 0.55 ~ 0.90 之間
- predicted_change_pct 應合理（{market_name}短期通常在 2%~15% 之間）
- stop_loss_price 應低於 current_price 3%~8%
- 只推薦你有信心的股票，寧缺勿濫"""

        # 嘗試 Gemini → Groq fallback
        result = self._call_gemini(prompt)
        if result is None:
            result = self._call_groq(prompt)

        if result is None:
            # 最終 fallback: 用技術分數排序
            return self._fallback_rank(candidates, market, top_n)

        # 解析並補充數據
        picks = result.get("picks", [])
        enriched = []
        for pick in picks[:top_n]:
            # 補充候選股的技術數據
            symbol = pick.get("symbol", "")
            cand = next((c for c in candidates if c["symbol"] == symbol), None)
            name = pick.get("name", "") or STOCK_NAMES.get(symbol, symbol)
            enriched.append({
                "stock_id": symbol,
                "name": name,
                "current_price": pick.get("current_price", cand["close"] if cand else 0),
                "predicted_change_pct": pick.get("predicted_change_pct", 0),
                "probability": min(0.95, max(0.5, pick.get("probability", 0.6))),
                "target_price": pick.get("target_price", 0),
                "stop_loss_price": pick.get("stop_loss_price", 0),
                "risk_level": pick.get("risk_level", "MEDIUM"),
                "reasoning": pick.get("reasoning", ""),
                "key_signals": pick.get("key_signals", []),
                "technical_score": cand["score"] if cand else 0,
                "rsi": cand["rsi"] if cand else 0,
                "change_5d": cand["change_5d"] if cand else 0,
                "market": market,
            })

        return enriched

    def _call_gemini(self, prompt: str) -> Optional[Dict]:
        """呼叫 Gemini API"""
        try:
            config = genai_types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=2048,
            )
            if self.subscription_tier == "pro":
                config.thinking = genai_types.ThinkingConfig(thinking_budget=5000)

            response = self.gemini_client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=config,
            )

            text = response.text.strip()
            # 清理 markdown 標記
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)

            return json.loads(text)
        except Exception as e:
            logger.warning(f"[Discovery] Gemini failed: {e}")
            return None

    def _call_groq(self, prompt: str) -> Optional[Dict]:
        """呼叫 Groq API (fallback)"""
        try:
            if not settings.GROQ_API_KEY:
                return None
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)
            response = client.chat.completions.create(
                model=settings.GROQ_MODEL or "llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "你是專業的短線交易分析師，只用 JSON 格式回覆。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2048,
            )
            text = response.choices[0].message.content.strip()
            if text.startswith("```"):
                lines = text.split("\n")
                lines = [l for l in lines if not l.strip().startswith("```")]
                text = "\n".join(lines)
            return json.loads(text)
        except Exception as e:
            logger.warning(f"[Discovery] Groq failed: {e}")
            return None

    def _fallback_rank(self, candidates: List[Dict], market: str, top_n: int) -> List[Dict]:
        """無 AI 時用技術分數直接排序"""
        picks = []
        for c in candidates[:top_n]:
            close = c["close"]
            symbol = c["symbol"]
            # 簡單估算目標價：技術分數越高，預期漲幅越大
            est_change = min(10, max(2, (c["score"] - 40) * 0.2))
            target = round(close * (1 + est_change / 100), 2)
            stop_loss = round(close * 0.95, 2)

            picks.append({
                "stock_id": symbol,
                "name": STOCK_NAMES.get(symbol, symbol),
                "current_price": close,
                "predicted_change_pct": round(est_change, 1),
                "probability": min(0.85, 0.5 + c["score"] / 200),
                "target_price": target,
                "stop_loss_price": stop_loss,
                "risk_level": "MEDIUM",
                "reasoning": f"技術面分數 {c['score']}，RSI={c['rsi']}，{c['macd_status']}",
                "key_signals": [
                    f"RSI {c['rsi']}",
                    f"MACD {c['macd_status']}",
                    f"均線 {c['ma_trend']}",
                ],
                "technical_score": c["score"],
                "rsi": c["rsi"],
                "change_5d": c["change_5d"],
                "market": market,
            })
        return picks

    def _generate_market_summary(self, picks: List[Dict], market: str) -> str:
        if not picks:
            return "市場整體偏弱，暫無明顯短期機會"
        avg_prob = sum(p.get("probability", 0) for p in picks) / len(picks)
        market_name = "台股" if market == "TW" else "美股"
        if avg_prob >= 0.75:
            return f"{market_name}短線偏多，AI 掃描到 {len(picks)} 支高機率潛力股"
        elif avg_prob >= 0.6:
            return f"{market_name}短線中性偏多，AI 篩選出 {len(picks)} 支值得關注的標的"
        else:
            return f"{market_name}短線訊號分歧，建議謹慎操作"
