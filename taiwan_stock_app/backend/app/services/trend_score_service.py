"""
趨勢強度分數服務

把多個技術指標濃縮成 0-100 的單一分數 + 白話結論，
讓使用者一眼看懂目前股票的趨勢狀態。

評分原則：
- 50 分 = 中性（多空拉鋸）
- 100 分 = 極強多
- 0 分   = 極強空

各維度貢獻一個介於 -滿分 ~ +滿分 的「方向分」，
最後依照權重總和正規化到 0-100。
"""
from typing import Dict, List, Optional
import logging
import pandas as pd

from app.services.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)


# 各維度權重（總和 100）
WEIGHTS = {
    "ma_alignment": 25,   # 均線排列
    "macd": 20,           # MACD
    "rsi": 15,            # RSI
    "kd": 15,             # KD
    "bollinger": 10,      # 布林通道位置
    "volume": 15,         # 量能配合
}


def _safe_last(series: pd.Series, offset: int = 0):
    """取得 series 倒數第 offset 個有效值"""
    if series is None or len(series) == 0:
        return None
    s = series.dropna()
    if len(s) <= offset:
        return None
    return float(s.iloc[-1 - offset])


def _score_ma_alignment(df: pd.DataFrame) -> Dict:
    """
    均線排列評分 (-25 ~ +25)
    多頭排列：MA5 > MA10 > MA20 > MA60 → +25
    空頭排列：反之 → -25
    部分排列：依符合的條件比例給分
    """
    max_score = WEIGHTS["ma_alignment"]
    close = df["close"]

    ma5 = _safe_last(TechnicalIndicators.calculate_ma(close, 5))
    ma10 = _safe_last(TechnicalIndicators.calculate_ma(close, 10))
    ma20 = _safe_last(TechnicalIndicators.calculate_ma(close, 20))
    ma60 = _safe_last(TechnicalIndicators.calculate_ma(close, 60))
    last_close = _safe_last(close)

    if None in (ma5, ma10, ma20, last_close):
        return {
            "name": "均線排列",
            "score": 0,
            "max": max_score,
            "signal": "資料不足",
            "weight": max_score,
        }

    # 三條件：MA5>MA10、MA10>MA20、MA20>MA60（若有）+ 收盤站上 MA20
    bullish_count = 0
    bearish_count = 0
    total = 4 if ma60 is not None else 3

    if ma5 > ma10:
        bullish_count += 1
    elif ma5 < ma10:
        bearish_count += 1

    if ma10 > ma20:
        bullish_count += 1
    elif ma10 < ma20:
        bearish_count += 1

    if ma60 is not None:
        if ma20 > ma60:
            bullish_count += 1
        elif ma20 < ma60:
            bearish_count += 1

    if last_close > ma20:
        bullish_count += 1
    elif last_close < ma20:
        bearish_count += 1

    net = bullish_count - bearish_count
    score = round(max_score * (net / total))

    # 訊號描述
    if bullish_count == total:
        signal = "完美多頭排列（MA5>MA10>MA20>MA60）"
    elif bearish_count == total:
        signal = "完美空頭排列（MA5<MA10<MA20<MA60）"
    elif net > 0:
        signal = f"偏多排列（{bullish_count}/{total} 條件成立）"
    elif net < 0:
        signal = f"偏空排列（{bearish_count}/{total} 條件成立）"
    else:
        signal = "均線糾結，方向不明"

    return {
        "name": "均線排列",
        "score": score,
        "max": max_score,
        "signal": signal,
        "weight": max_score,
        "details": {
            "ma5": round(ma5, 2),
            "ma10": round(ma10, 2),
            "ma20": round(ma20, 2),
            "ma60": round(ma60, 2) if ma60 else None,
            "close": round(last_close, 2),
        },
    }


def _score_macd(df: pd.DataFrame) -> Dict:
    """
    MACD 評分 (-20 ~ +20)
    黃金交叉（最近 3 日內） → +20
    死亡交叉（最近 3 日內） → -20
    MACD > Signal 且 histogram 上升 → +12
    MACD < Signal 且 histogram 下降 → -12
    """
    max_score = WEIGHTS["macd"]
    macd_data = TechnicalIndicators.calculate_macd(df["close"])
    macd_now = _safe_last(macd_data["macd"])
    sig_now = _safe_last(macd_data["signal"])
    hist_now = _safe_last(macd_data["histogram"])
    hist_prev = _safe_last(macd_data["histogram"], offset=1)

    if None in (macd_now, sig_now, hist_now):
        return {
            "name": "MACD",
            "score": 0,
            "max": max_score,
            "signal": "資料不足",
            "weight": max_score,
        }

    # 偵測最近 3 日內是否發生交叉
    cross = None
    macd_series = macd_data["macd"].dropna().tolist()
    sig_series = macd_data["signal"].dropna().tolist()
    n = min(len(macd_series), len(sig_series))
    for i in range(1, min(4, n)):
        cur_diff = macd_series[-i] - sig_series[-i]
        prev_diff = macd_series[-i - 1] - sig_series[-i - 1] if n > i + 1 else cur_diff
        if prev_diff <= 0 and cur_diff > 0:
            cross = "golden"
            break
        elif prev_diff >= 0 and cur_diff < 0:
            cross = "death"
            break

    if cross == "golden":
        return {
            "name": "MACD",
            "score": max_score,
            "max": max_score,
            "signal": "近期黃金交叉，動能轉強",
            "weight": max_score,
            "details": {"macd": round(macd_now, 3), "signal": round(sig_now, 3), "histogram": round(hist_now, 3)},
        }
    if cross == "death":
        return {
            "name": "MACD",
            "score": -max_score,
            "max": max_score,
            "signal": "近期死亡交叉，動能轉弱",
            "weight": max_score,
            "details": {"macd": round(macd_now, 3), "signal": round(sig_now, 3), "histogram": round(hist_now, 3)},
        }

    # 無交叉，看 histogram 走向
    hist_rising = hist_prev is not None and hist_now > hist_prev

    if macd_now > sig_now and hist_rising:
        return {"name": "MACD", "score": 12, "max": max_score,
                "signal": "MACD 在訊號線上方且柱狀圖擴大", "weight": max_score}
    if macd_now > sig_now:
        return {"name": "MACD", "score": 6, "max": max_score,
                "signal": "MACD 在訊號線上方但動能減弱", "weight": max_score}
    if macd_now < sig_now and not hist_rising:
        return {"name": "MACD", "score": -12, "max": max_score,
                "signal": "MACD 在訊號線下方且柱狀圖擴大", "weight": max_score}
    return {"name": "MACD", "score": -6, "max": max_score,
            "signal": "MACD 在訊號線下方但跌勢趨緩", "weight": max_score}


def _score_rsi(df: pd.DataFrame) -> Dict:
    """
    RSI 評分 (-15 ~ +15)
    50-70 健康多頭 → +10
    >70 超買 → -5（過熱反向警示）
    30-50 健康空頭 → -10
    <30 超賣 → +5（反彈機會）
    接近 50 → 0
    """
    max_score = WEIGHTS["rsi"]
    rsi = _safe_last(TechnicalIndicators.calculate_rsi(df["close"]))

    if rsi is None:
        return {"name": "RSI", "score": 0, "max": max_score, "signal": "資料不足", "weight": max_score}

    if rsi >= 80:
        return {"name": "RSI", "score": -10, "max": max_score,
                "signal": f"RSI {rsi:.1f}，明顯超買，注意拉回", "weight": max_score,
                "details": {"rsi": round(rsi, 1)}}
    if rsi >= 70:
        return {"name": "RSI", "score": -5, "max": max_score,
                "signal": f"RSI {rsi:.1f}，進入超買區", "weight": max_score,
                "details": {"rsi": round(rsi, 1)}}
    if rsi >= 55:
        return {"name": "RSI", "score": max_score, "max": max_score,
                "signal": f"RSI {rsi:.1f}，多方力道強勁", "weight": max_score,
                "details": {"rsi": round(rsi, 1)}}
    if rsi >= 50:
        return {"name": "RSI", "score": 8, "max": max_score,
                "signal": f"RSI {rsi:.1f}，多方略佔優", "weight": max_score,
                "details": {"rsi": round(rsi, 1)}}
    if rsi >= 45:
        return {"name": "RSI", "score": -8, "max": max_score,
                "signal": f"RSI {rsi:.1f}，空方略佔優", "weight": max_score,
                "details": {"rsi": round(rsi, 1)}}
    if rsi >= 30:
        return {"name": "RSI", "score": -max_score, "max": max_score,
                "signal": f"RSI {rsi:.1f}，空方力道強勁", "weight": max_score,
                "details": {"rsi": round(rsi, 1)}}
    if rsi >= 20:
        return {"name": "RSI", "score": 5, "max": max_score,
                "signal": f"RSI {rsi:.1f}，進入超賣區，留意反彈", "weight": max_score,
                "details": {"rsi": round(rsi, 1)}}
    return {"name": "RSI", "score": 10, "max": max_score,
            "signal": f"RSI {rsi:.1f}，明顯超賣，反彈機率升高", "weight": max_score,
            "details": {"rsi": round(rsi, 1)}}


def _score_kd(df: pd.DataFrame) -> Dict:
    """
    KD 評分 (-15 ~ +15)
    """
    max_score = WEIGHTS["kd"]
    kd_data = TechnicalIndicators.calculate_kd(df["high"], df["low"], df["close"])
    k_now = _safe_last(kd_data["k"])
    d_now = _safe_last(kd_data["d"])
    k_prev = _safe_last(kd_data["k"], offset=1)
    d_prev = _safe_last(kd_data["d"], offset=1)

    if None in (k_now, d_now):
        return {"name": "KD", "score": 0, "max": max_score, "signal": "資料不足", "weight": max_score}

    # 偵測交叉
    cross = None
    if k_prev is not None and d_prev is not None:
        prev_diff = k_prev - d_prev
        cur_diff = k_now - d_now
        if prev_diff <= 0 and cur_diff > 0:
            cross = "golden"
        elif prev_diff >= 0 and cur_diff < 0:
            cross = "death"

    details = {"k": round(k_now, 1), "d": round(d_now, 1)}

    # 高檔死叉、低檔金叉特別敏感
    if cross == "golden" and k_now < 30:
        return {"name": "KD", "score": max_score, "max": max_score,
                "signal": f"KD 低檔黃金交叉（K={k_now:.1f}），反彈訊號明確",
                "weight": max_score, "details": details}
    if cross == "death" and k_now > 70:
        return {"name": "KD", "score": -max_score, "max": max_score,
                "signal": f"KD 高檔死亡交叉（K={k_now:.1f}），轉弱訊號明確",
                "weight": max_score, "details": details}
    if cross == "golden":
        return {"name": "KD", "score": 10, "max": max_score,
                "signal": f"KD 黃金交叉（K={k_now:.1f}）", "weight": max_score, "details": details}
    if cross == "death":
        return {"name": "KD", "score": -10, "max": max_score,
                "signal": f"KD 死亡交叉（K={k_now:.1f}）", "weight": max_score, "details": details}

    # 無交叉，看絕對位置 + K vs D
    if k_now > 80:
        return {"name": "KD", "score": -5, "max": max_score,
                "signal": f"KD 進入超買區（K={k_now:.1f}）", "weight": max_score, "details": details}
    if k_now < 20:
        return {"name": "KD", "score": 5, "max": max_score,
                "signal": f"KD 進入超賣區（K={k_now:.1f}）", "weight": max_score, "details": details}
    if k_now > d_now:
        return {"name": "KD", "score": 6, "max": max_score,
                "signal": f"K({k_now:.1f}) 在 D({d_now:.1f}) 上方", "weight": max_score, "details": details}
    return {"name": "KD", "score": -6, "max": max_score,
            "signal": f"K({k_now:.1f}) 在 D({d_now:.1f}) 下方", "weight": max_score, "details": details}


def _score_bollinger(df: pd.DataFrame) -> Dict:
    """
    布林通道位置評分 (-10 ~ +10)
    收盤靠近上軌 → +5（強勢但接近超買）
    中軌之上 → +5
    中軌之下 → -5
    靠近下軌 → -5（弱勢但接近超賣）
    跌破下軌 → -10（破底）
    突破上軌 → +10（強勢突破）
    """
    max_score = WEIGHTS["bollinger"]
    bb = TechnicalIndicators.calculate_bollinger_bands(df["close"])
    upper = _safe_last(bb["upper"])
    middle = _safe_last(bb["middle"])
    lower = _safe_last(bb["lower"])
    close = _safe_last(df["close"])

    if None in (upper, middle, lower, close):
        return {"name": "布林通道", "score": 0, "max": max_score, "signal": "資料不足", "weight": max_score}

    band_width = upper - lower
    if band_width <= 0:
        return {"name": "布林通道", "score": 0, "max": max_score, "signal": "通道收斂", "weight": max_score}

    pos = (close - lower) / band_width  # 0=下軌, 0.5=中軌, 1=上軌
    details = {"close": round(close, 2), "upper": round(upper, 2),
               "middle": round(middle, 2), "lower": round(lower, 2),
               "position_pct": round(pos * 100, 1)}

    if close > upper:
        return {"name": "布林通道", "score": max_score, "max": max_score,
                "signal": "突破上軌，強勢但留意過熱", "weight": max_score, "details": details}
    if close < lower:
        return {"name": "布林通道", "score": -max_score, "max": max_score,
                "signal": "跌破下軌，弱勢但留意超賣反彈", "weight": max_score, "details": details}
    if pos >= 0.7:
        return {"name": "布林通道", "score": 5, "max": max_score,
                "signal": "靠近上軌，多方氣勢強", "weight": max_score, "details": details}
    if pos >= 0.5:
        return {"name": "布林通道", "score": 3, "max": max_score,
                "signal": "在中軌上方", "weight": max_score, "details": details}
    if pos >= 0.3:
        return {"name": "布林通道", "score": -3, "max": max_score,
                "signal": "在中軌下方", "weight": max_score, "details": details}
    return {"name": "布林通道", "score": -5, "max": max_score,
            "signal": "靠近下軌，空方氣勢強", "weight": max_score, "details": details}


def _score_volume(df: pd.DataFrame) -> Dict:
    """
    量能配合評分 (-15 ~ +15)
    5日均量 / 20日均量 > 1.2 且當日漲 → +15（價漲量增）
    > 1.2 且當日跌 → -15（價跌量增，賣壓重）
    < 0.8 量縮：盤整訊號，依價格方向給小分
    """
    max_score = WEIGHTS["volume"]
    if "volume" not in df.columns or len(df) < 21:
        return {"name": "量能", "score": 0, "max": max_score, "signal": "資料不足", "weight": max_score}

    vol = df["volume"]
    close = df["close"]
    ma5_vol = vol.rolling(5).mean()
    ma20_vol = vol.rolling(20).mean()

    v5 = _safe_last(ma5_vol)
    v20 = _safe_last(ma20_vol)
    today_close = _safe_last(close)
    yest_close = _safe_last(close, offset=1)

    if None in (v5, v20, today_close, yest_close) or v20 <= 0:
        return {"name": "量能", "score": 0, "max": max_score, "signal": "資料不足", "weight": max_score}

    ratio = v5 / v20
    price_up = today_close > yest_close
    details = {"vol_ratio_5_20": round(ratio, 2)}

    if ratio > 1.5 and price_up:
        return {"name": "量能", "score": max_score, "max": max_score,
                "signal": f"明顯價漲量增（量比 {ratio:.2f}）", "weight": max_score, "details": details}
    if ratio > 1.5 and not price_up:
        return {"name": "量能", "score": -max_score, "max": max_score,
                "signal": f"明顯價跌量增，賣壓沉重（量比 {ratio:.2f}）", "weight": max_score, "details": details}
    if ratio > 1.2 and price_up:
        return {"name": "量能", "score": 10, "max": max_score,
                "signal": f"價漲量增（量比 {ratio:.2f}）", "weight": max_score, "details": details}
    if ratio > 1.2 and not price_up:
        return {"name": "量能", "score": -10, "max": max_score,
                "signal": f"價跌量增（量比 {ratio:.2f}）", "weight": max_score, "details": details}
    if ratio < 0.7:
        sig = "量縮整理，動能不足" if price_up else "量縮下跌，跌勢趨緩"
        score = -3 if price_up else 3  # 量縮上漲不健康；量縮下跌反而是好事
        return {"name": "量能", "score": score, "max": max_score,
                "signal": f"{sig}（量比 {ratio:.2f}）", "weight": max_score, "details": details}
    return {"name": "量能", "score": 0, "max": max_score,
            "signal": f"量能持平（量比 {ratio:.2f}）", "weight": max_score, "details": details}


def _make_verdict(score: int) -> Dict:
    """根據分數產生結論文字"""
    if score >= 80:
        return {"verdict": "強多", "color": "strong_bull",
                "summary": "各項指標一面倒看好，多方氣勢強，但要小心追高與短線過熱。"}
    if score >= 65:
        return {"verdict": "偏多", "color": "bull",
                "summary": "趨勢偏向上漲，可考慮逢低布局或順勢操作。"}
    if score >= 55:
        return {"verdict": "略偏多", "color": "weak_bull",
                "summary": "多空略偏多方，但訊號不夠強，宜觀察後續確認。"}
    if score >= 45:
        return {"verdict": "中性", "color": "neutral",
                "summary": "多空拉鋸，方向不明，建議觀望或等待突破訊號。"}
    if score >= 35:
        return {"verdict": "略偏空", "color": "weak_bear",
                "summary": "多空略偏空方，宜減碼或暫緩進場。"}
    if score >= 20:
        return {"verdict": "偏空", "color": "bear",
                "summary": "趨勢偏向下跌，注意停損與避免逆勢承接。"}
    return {"verdict": "強空", "color": "strong_bear",
            "summary": "全面走弱，避免進場，已持有可考慮停損。"}


def calculate_trend_score(df: pd.DataFrame) -> Optional[Dict]:
    """
    根據歷史 K 線計算趨勢強度分數

    Args:
        df: 包含 open/high/low/close/volume 的 DataFrame，須至少 60 筆

    Returns:
        {
            "score": 0-100,
            "verdict": "強多/偏多/...",
            "color": "strong_bull/bull/...",
            "summary": "白話結論",
            "breakdown": [...各維度分數...],
            "highlights": [...特殊訊號清單...],
        }
    """
    if df is None or len(df) < 30:
        return None

    breakdowns = [
        _score_ma_alignment(df),
        _score_macd(df),
        _score_rsi(df),
        _score_kd(df),
        _score_bollinger(df),
        _score_volume(df),
    ]

    # 加總方向分（-滿分 ~ +滿分）
    total_directional = sum(b["score"] for b in breakdowns)
    total_max = sum(b["max"] for b in breakdowns)

    if total_max <= 0:
        return None

    # normalize 到 0-100，50=中性
    normalized = 50 + (total_directional / total_max) * 50
    score = max(0, min(100, round(normalized)))

    verdict = _make_verdict(score)

    # 篩選關鍵訊號（黃金/死亡交叉、超買超賣、價量背離）
    highlights = []
    for b in breakdowns:
        sig = b.get("signal", "")
        if any(kw in sig for kw in ["黃金交叉", "死亡交叉", "超買", "超賣", "突破", "跌破", "量增"]):
            highlights.append({"category": b["name"], "text": sig,
                               "tone": "positive" if b["score"] > 0 else "negative"})

    return {
        "score": score,
        "verdict": verdict["verdict"],
        "color": verdict["color"],
        "summary": verdict["summary"],
        "breakdown": breakdowns,
        "highlights": highlights,
    }
