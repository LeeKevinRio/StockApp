"""
Enhanced Sentiment Analyzer — AI 語意情緒分析升級版
取代簡單的關鍵字計數，改用更精確的上下文感知情緒分析

特色：
1. 否定詞處理（「不看好」→ 負面）
2. 強度修飾詞（「大漲」比「漲」更強）
3. 財經專業術語辨識
4. 上下文窗口分析（前後文影響情緒方向）
5. Threads/PTT/Dcard 各平台語言風格適配
"""
import re
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


class EnhancedSentimentAnalyzer:
    """進階中文財經情緒分析器"""

    # ===== 否定詞 =====
    NEGATION_WORDS = {"不", "沒", "未", "非", "別", "無", "難", "否", "莫", "勿", "甭"}

    # ===== 強度修飾詞 =====
    INTENSITY_AMPLIFIERS = {
        "大": 1.5, "超": 1.5, "爆": 1.8, "狂": 1.6, "猛": 1.5,
        "暴": 1.7, "瘋": 1.6, "極": 1.6, "巨": 1.5, "狠": 1.5,
        "強力": 1.4, "明顯": 1.3, "顯著": 1.3, "持續": 1.2, "連續": 1.3,
    }
    INTENSITY_DAMPENERS = {
        "微": 0.5, "小": 0.6, "略": 0.5, "稍": 0.5, "些": 0.6,
        "可能": 0.7, "或許": 0.6, "也許": 0.6, "預期": 0.8,
    }

    # ===== 帶分數的情緒詞典（-1.0 ~ +1.0）=====
    SENTIMENT_LEXICON = {
        # 強正面 (0.7 ~ 1.0)
        "飆漲": 0.9, "暴漲": 0.9, "噴出": 0.85, "爆噴": 0.9, "起飛": 0.8,
        "漲停": 0.9, "創新高": 0.85, "翻倍": 0.9, "大漲": 0.8, "強漲": 0.8,
        "發大財": 0.8, "梭哈": 0.75, "all in": 0.75,

        # 中正面 (0.3 ~ 0.7)
        "漲": 0.5, "買進": 0.55, "進場": 0.55, "加碼": 0.5, "看多": 0.6,
        "利多": 0.65, "突破": 0.6, "紅盤": 0.5, "反彈": 0.5, "上攻": 0.55,
        "賺": 0.5, "獲利": 0.5, "看好": 0.55, "樂觀": 0.5, "強勢": 0.55,
        "上漲": 0.5, "回升": 0.45, "營收增": 0.55, "成長": 0.5,
        "超預期": 0.6, "上車": 0.5, "多方": 0.5, "做多": 0.55,
        "黃金交叉": 0.6, "量增價漲": 0.6, "底部翻揚": 0.6,
        "法人買超": 0.55, "外資買超": 0.6, "投信買超": 0.55,

        # 弱正面 (0.1 ~ 0.3)
        "持平": 0.1, "穩定": 0.2, "偏多": 0.25, "小漲": 0.25, "溫和": 0.15,

        # 弱負面 (-0.1 ~ -0.3)
        "偏空": -0.25, "觀望": -0.15, "壓力": -0.2, "疲弱": -0.25,
        "小跌": -0.25, "整理": -0.1, "盤整": -0.1,

        # 中負面 (-0.3 ~ -0.7)
        "跌": -0.5, "賣出": -0.55, "出場": -0.55, "減碼": -0.5, "看空": -0.6,
        "利空": -0.65, "跌破": -0.6, "綠盤": -0.5, "下跌": -0.5, "走低": -0.5,
        "虧損": -0.55, "套牢": -0.6, "看壞": -0.55, "悲觀": -0.5, "弱勢": -0.5,
        "營收減": -0.55, "衰退": -0.55, "下車": -0.5, "空方": -0.5, "做空": -0.55,
        "死亡交叉": -0.6, "量縮價跌": -0.6, "頭部反轉": -0.6,
        "法人賣超": -0.55, "外資賣超": -0.6, "投信賣超": -0.55,

        # 強負面 (-0.7 ~ -1.0)
        "暴跌": -0.9, "崩盤": -0.9, "跌停": -0.9, "腰斬": -0.85, "大跌": -0.8,
        "重挫": -0.8, "慘跌": -0.85, "恐慌": -0.8, "逃命": -0.8, "殺盤": -0.75,
        "破底": -0.8, "斷頭": -0.85, "融斷": -0.9,
    }

    # ===== 英文情緒詞典（用於 Threads 英文內容）=====
    EN_SENTIMENT_LEXICON = {
        "surge": 0.7, "soar": 0.7, "rally": 0.6, "moon": 0.8,
        "rocket": 0.75, "bullish": 0.6, "breakout": 0.65, "gains": 0.5,
        "beat": 0.55, "upgrade": 0.6, "buy": 0.5, "strong": 0.5,
        "all-time high": 0.8, "record high": 0.8,
        "crash": -0.8, "plunge": -0.8, "dump": -0.7, "bearish": -0.6,
        "sell": -0.5, "miss": -0.55, "downgrade": -0.6, "weak": -0.5,
        "bankruptcy": -0.9, "lawsuit": -0.5, "layoff": -0.55,
    }

    # ===== PTT 專屬語言（鄉民用語）=====
    PTT_SLANG = {
        "推": 0.3, "噓": -0.4, "朝聖": 0.2, "卡位": 0.3,
        "GG": -0.6, "QQ": -0.4, "777": 0.4, "信仰": 0.3,
        "抄底": 0.5, "割肉": -0.6, "韭菜": -0.4, "散戶": -0.1,
        "主力": 0.2, "籌碼集中": 0.4, "被套": -0.6, "解套": 0.4,
        "軋空": 0.6, "嘎空": 0.6, "空手": -0.1, "滿手": 0.2,
    }

    def analyze(self, text: str, platform: str = "general",
                push_count: int = 0, boo_count: int = 0) -> Dict:
        """
        進階情緒分析

        Args:
            text: 要分析的文字
            platform: 平台來源 (ptt, dcard, threads, mobile01, general)
            push_count: 推文數（PTT）
            boo_count: 噓文數（PTT）

        Returns:
            dict with sentiment, score, confidence, details
        """
        if not text:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.0, "details": {}}

        # 1. 中文詞典分析
        zh_score, zh_matches = self._analyze_chinese(text, platform)

        # 2. 英文詞典分析（Threads 可能有英文內容）
        en_score, en_matches = self._analyze_english(text)

        # 3. 反應數據加權（PTT 推/噓）
        reaction_score = 0.0
        if push_count + boo_count > 0:
            reaction_score = (push_count - boo_count) / (push_count + boo_count)

        # 4. 綜合加權
        total_matches = len(zh_matches) + len(en_matches)
        if total_matches == 0 and (push_count + boo_count) == 0:
            return {"sentiment": "neutral", "score": 0.0, "confidence": 0.1, "details": {"no_signal": True}}

        # 文字情緒 vs 反應情緒的權重
        text_weight = 0.65
        reaction_weight = 0.35 if (push_count + boo_count) > 0 else 0.0

        text_score = zh_score if abs(zh_score) > abs(en_score) else (zh_score * 0.6 + en_score * 0.4)
        if reaction_weight > 0:
            final_score = text_score * text_weight + reaction_score * reaction_weight
        else:
            final_score = text_score

        # 限制在 -1 ~ 1
        final_score = max(-1.0, min(1.0, final_score))

        # 信心度：基於匹配的詞數和一致性
        confidence = min(1.0, total_matches * 0.15 + 0.2)
        if total_matches > 0:
            # 如果正負詞都多，信心度降低（矛盾訊號）
            pos_matches = sum(1 for _, s in (zh_matches + en_matches) if s > 0)
            neg_matches = sum(1 for _, s in (zh_matches + en_matches) if s < 0)
            if pos_matches > 0 and neg_matches > 0:
                consistency = abs(pos_matches - neg_matches) / (pos_matches + neg_matches)
                confidence *= (0.5 + 0.5 * consistency)

        # 判斷情緒標籤
        if final_score >= 0.5:
            sentiment = "very_positive"
        elif final_score >= 0.15:
            sentiment = "positive"
        elif final_score <= -0.5:
            sentiment = "very_negative"
        elif final_score <= -0.15:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        return {
            "sentiment": sentiment,
            "score": round(final_score, 3),
            "confidence": round(confidence, 2),
            "details": {
                "zh_score": round(zh_score, 3),
                "en_score": round(en_score, 3),
                "reaction_score": round(reaction_score, 3),
                "match_count": total_matches,
                "top_signals": [m[0] for m in sorted(zh_matches + en_matches, key=lambda x: abs(x[1]), reverse=True)[:5]],
            }
        }

    def _analyze_chinese(self, text: str, platform: str) -> Tuple[float, List[Tuple[str, float]]]:
        """中文情緒分析（含否定詞和強度修飾）"""
        matches = []
        scores = []

        # 合併平台專屬詞典
        lexicon = dict(self.SENTIMENT_LEXICON)
        if platform == "ptt":
            lexicon.update(self.PTT_SLANG)

        # 按詞長降序排列（避免短詞先匹配覆蓋長詞）
        sorted_terms = sorted(lexicon.keys(), key=len, reverse=True)

        processed_positions = set()

        for term in sorted_terms:
            pos = 0
            while True:
                idx = text.find(term, pos)
                if idx == -1:
                    break

                # 檢查該位置是否已被較長的詞覆蓋
                term_range = set(range(idx, idx + len(term)))
                if term_range & processed_positions:
                    pos = idx + 1
                    continue

                base_score = lexicon[term]

                # 檢查否定詞（前面2字內）
                prefix = text[max(0, idx - 2):idx]
                negated = any(neg in prefix for neg in self.NEGATION_WORDS)
                if negated:
                    base_score = -base_score * 0.8  # 否定不完全反轉

                # 檢查強度修飾詞（前面3字內）
                prefix3 = text[max(0, idx - 3):idx]
                for amp, multiplier in self.INTENSITY_AMPLIFIERS.items():
                    if amp in prefix3:
                        base_score *= multiplier
                        break
                for damp, multiplier in self.INTENSITY_DAMPENERS.items():
                    if damp in prefix3:
                        base_score *= multiplier
                        break

                matches.append((term, base_score))
                scores.append(base_score)
                processed_positions.update(term_range)
                pos = idx + len(term)

        if not scores:
            return 0.0, matches

        # 加權平均（較強的訊號權重更高）
        weighted_sum = sum(s * abs(s) for s in scores)
        weight_total = sum(abs(s) for s in scores)
        avg_score = weighted_sum / weight_total if weight_total > 0 else 0.0

        return max(-1.0, min(1.0, avg_score)), matches

    def _analyze_english(self, text: str) -> Tuple[float, List[Tuple[str, float]]]:
        """英文情緒分析"""
        text_lower = text.lower()
        matches = []
        scores = []

        for term, score in self.EN_SENTIMENT_LEXICON.items():
            if term in text_lower:
                matches.append((term, score))
                scores.append(score)

        if not scores:
            return 0.0, matches

        avg_score = sum(scores) / len(scores)
        return max(-1.0, min(1.0, avg_score)), matches

    def batch_analyze(self, posts: List[Dict], platform: str = "general") -> List[Dict]:
        """
        批次分析多篇貼文

        Args:
            posts: 貼文列表，每個需有 title（和可選的 content）
            platform: 平台來源

        Returns:
            更新後的貼文列表，每個附加 enhanced_sentiment
        """
        for post in posts:
            text = f"{post.get('title', '')} {post.get('content', '')}"
            push = post.get("push_count", 0)
            boo = post.get("boo_count", 0)

            result = self.analyze(text, platform, push, boo)
            post["enhanced_sentiment"] = result
            # 同時更新舊欄位保持相容
            post["sentiment"] = result["sentiment"].replace("very_", "")
            post["sentiment_score"] = result["score"]

        return posts


# 全域實例
enhanced_analyzer = EnhancedSentimentAnalyzer()
