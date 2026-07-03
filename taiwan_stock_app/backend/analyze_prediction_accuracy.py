"""
預測準確率歸因分析腳本

用途：回答「準確率為什麼低、哪個面向在扯後腿」，取代憑感覺調權重。
用法：
    python analyze_prediction_accuracy.py            # 全部已驗證紀錄
    python analyze_prediction_accuracy.py --market TW  # 只看台股

分析維度：
1. 整體 / 分市場方向準確率
2. 分 AI 提供者（Gemini / Groq / Mock）— 檢查 Mock fallback 是否拖累整體
3. 預測方向偏誤（UP vs DOWN 的比例與各自命中率）
4. 信心度校準（預測機率 70% 的那批實際命中率是否接近 70%）
5. 各面向分數歸因（需要 analysis_scores 快照，2026-07 之後的紀錄才有）—
   每個面向「看多時實際上漲、看空時實際下跌」的命中率
"""
import sys
import json
from collections import defaultdict

from app.database import SessionLocal
from app.models import PredictionRecord

# 面向分數快照的鍵 → 顯示名稱
DIMENSIONS = [
    ("technical", "技術面"),
    ("chip", "籌碼面"),
    ("fundamental", "基本面"),
    ("news_sentiment", "消息面"),
    ("social_sentiment", "社群面"),
    ("macro", "宏觀面"),
    ("total_weighted", "加權總分"),
    ("prediction_score", "預測分數"),
]

# 面向訊號門檻：|分數| >= 此值才視為「有表態」，避免 0 分雜訊稀釋統計
SIGNAL_THRESHOLD = 10


def pct(x, n):
    return f"{x / n * 100:.1f}%" if n > 0 else "N/A"


def line(char="-", width=64):
    print(char * width)


def main():
    market_filter = None
    if "--market" in sys.argv:
        idx = sys.argv.index("--market")
        if idx + 1 < len(sys.argv):
            market_filter = sys.argv[idx + 1].upper()

    db = SessionLocal()
    try:
        query = db.query(PredictionRecord).filter(
            PredictionRecord.actual_close_price.isnot(None),
            PredictionRecord.direction_correct.isnot(None),
        )
        if market_filter:
            query = query.filter(PredictionRecord.market_region == market_filter)
        records = query.order_by(PredictionRecord.target_date.asc()).all()

        if not records:
            print("沒有已驗證的預測紀錄。請先讓排程跑幾天，或執行 update_actual_results。")
            return

        n = len(records)
        correct = sum(1 for r in records if r.direction_correct)
        avg_err = sum(float(r.error_percent or 0) for r in records) / n

        line("=")
        print(f"預測準確率歸因分析  （{records[0].target_date} ~ {records[-1].target_date}）")
        line("=")
        print(f"總樣本：{n} 筆　方向準確率：{pct(correct, n)}　平均誤差：{avg_err:.2f}%")

        # ===== 1. 分市場 =====
        line()
        print("【分市場】")
        by_market = defaultdict(list)
        for r in records:
            by_market[r.market_region or "?"].append(r)
        for mkt, rs in sorted(by_market.items()):
            c = sum(1 for r in rs if r.direction_correct)
            print(f"  {mkt}: {len(rs)} 筆，方向準確率 {pct(c, len(rs))}")

        # ===== 2. 分 AI 提供者（Mock 是否在扯後腿）=====
        line()
        print("【分 AI 提供者】※ Mock 佔比高或準確率低代表 API 備援太常觸發")
        by_provider = defaultdict(list)
        for r in records:
            by_provider[r.ai_provider or "Unknown"].append(r)
        for prov, rs in sorted(by_provider.items(), key=lambda x: -len(x[1])):
            c = sum(1 for r in rs if r.direction_correct)
            print(f"  {prov}: {len(rs)} 筆（佔 {pct(len(rs), n)}），方向準確率 {pct(c, len(rs))}")

        # ===== 3. 方向偏誤 =====
        line()
        print("【方向偏誤】※ 若某方向佔比極高且命中率 < 50%，代表系統性偏誤")
        for direction in ("UP", "DOWN"):
            rs = [r for r in records if r.predicted_direction == direction]
            c = sum(1 for r in rs if r.direction_correct)
            print(f"  預測 {direction}: {len(rs)} 筆（佔 {pct(len(rs), n)}），命中率 {pct(c, len(rs))}")
        actual_up = sum(1 for r in records if r.actual_direction == "UP")
        print(f"  （實際上漲比例：{pct(actual_up, n)}，可作為基準線）")

        # ===== 4. 信心度校準 =====
        line()
        print("【信心度校準】※ 預測機率應接近實際命中率，偏高代表過度自信")
        buckets = [(0.0, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 0.70), (0.70, 0.75), (0.75, 1.01)]
        for lo, hi in buckets:
            rs = [r for r in records if lo <= float(r.predicted_probability or 0) < hi]
            if not rs:
                continue
            c = sum(1 for r in rs if r.direction_correct)
            print(f"  信心 {lo:.0%}~{hi - 0.01:.0%}: {len(rs)} 筆，實際命中 {pct(c, len(rs))}")

        # ===== 5. 各面向歸因（需 analysis_scores 快照）=====
        line()
        print(f"【各面向歸因】※ 訊號門檻 |分數| >= {SIGNAL_THRESHOLD}；命中率 < 50% 的面向在扯後腿")
        scored = []
        for r in records:
            scores = r.analysis_scores
            if isinstance(scores, str):
                try:
                    scores = json.loads(scores)
                except (ValueError, TypeError):
                    scores = None
            if isinstance(scores, dict) and r.actual_direction in ("UP", "DOWN"):
                scored.append((r, scores))

        if not scored:
            print("  尚無帶面向分數快照的已驗證紀錄（快照從 2026-07-03 之後的預測開始記錄），")
            print("  請累積約 2 週資料後再跑此分析。")
        else:
            print(f"  有快照的樣本：{len(scored)} 筆")
            for key, label in DIMENSIONS:
                hits = 0
                total = 0
                for r, scores in scored:
                    val = scores.get(key)
                    if val is None:
                        continue
                    try:
                        val = float(val)
                    except (TypeError, ValueError):
                        continue
                    if abs(val) < SIGNAL_THRESHOLD:
                        continue  # 面向未表態，不計入
                    total += 1
                    signal_up = val > 0
                    actual_up_flag = r.actual_direction == "UP"
                    if signal_up == actual_up_flag:
                        hits += 1
                if total > 0:
                    flag = " ⚠️ 低於隨機" if hits / total < 0.5 else ""
                    print(f"  {label:<6}: 表態 {total} 次，方向命中 {pct(hits, total)}{flag}")
                else:
                    print(f"  {label:<6}: 無有效表態樣本")

        line("=")
        print("解讀指引：")
        print("- Mock 佔比 > 20% → 優先修 API 金鑰/配額，比調權重有效")
        print("- 某面向命中率明顯 < 50% 且表態次數夠多 → 調低該面向權重（PREDICTION_WEIGHTS_TW）")
        print("- 某面向命中率 > 55% → 可考慮調高權重")
        print("- 信心度校準偏高 → 系統過度自信，屬顯示問題而非訊號問題")
    finally:
        db.close()


if __name__ == "__main__":
    main()
