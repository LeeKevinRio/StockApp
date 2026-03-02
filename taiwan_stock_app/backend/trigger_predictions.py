"""手動觸發為所有自選股生成 AI 預測（讀取 .env 設定）
支援：
  python trigger_predictions.py          # 只補齊今天缺少的預測
  python trigger_predictions.py --all    # 強制重新生成全部預測
"""
import sys
import time
from datetime import date
from app.database import SessionLocal
from app.models import Watchlist, Stock, User, PredictionRecord
from app.services.prediction_tracker import PredictionTracker
from app.services.ai_suggestion_service import AISuggestionService
from app.services.trading_calendar import get_next_trading_date


def main():
    force_all = "--all" in sys.argv
    db = SessionLocal()
    prediction_tracker = PredictionTracker()
    today = date.today()

    try:
        watchlist_items = db.query(Watchlist, Stock, User).join(
            Stock, Watchlist.stock_id == Stock.stock_id
        ).join(
            User, Watchlist.user_id == User.id
        ).all()

        # 去重
        seen = set()
        unique_items = []
        for wl, stock, user in watchlist_items:
            key = f"{stock.stock_id}_{stock.market_region}"
            if key not in seen:
                seen.add(key)
                unique_items.append((wl, stock, user))

        # 找出今天已有預測的股票
        existing_ids = set()
        if not force_all:
            existing_ids = set(
                r.stock_id for r in db.query(PredictionRecord.stock_id).filter(
                    PredictionRecord.prediction_date == today
                ).all()
            )

        # 計算需要生成的
        to_generate = [
            (wl, stock, user) for wl, stock, user in unique_items
            if force_all or stock.stock_id not in existing_ids
        ]

        mode = "強制全部重新生成" if force_all else "只補齊缺少的"
        print(f"自選股共 {len(unique_items)} 支，已有預測 {len(existing_ids)} 支")
        print(f"模式: {mode}，需要生成: {len(to_generate)} 支")
        print("=" * 50)

        if not to_generate:
            print("\n所有自選股今天都已有預測，無需生成！")
            return

        success = 0
        skipped = 0
        failed = 0

        for i, (wl, stock, user) in enumerate(to_generate, 1):
            try:
                market = stock.market_region or "TW"
                print(f"\n[{i}/{len(to_generate)}] {stock.stock_id} {stock.name} ({market})...", flush=True)

                service = AISuggestionService.for_user(user)
                suggestion = service.generate_suggestion(stock.stock_id, stock.name, market=market)

                if suggestion and suggestion.get("next_day_prediction"):
                    latest_price = suggestion.get("analysis_scores", {}).get("latest_price")
                    if not latest_price or float(latest_price) <= 0:
                        print(f"  SKIP: 無有效價格 (latest_price={latest_price})", flush=True)
                        skipped += 1
                        continue

                    prediction_tracker.save_prediction(
                        db=db,
                        stock_id=stock.stock_id,
                        stock_name=stock.name,
                        market=market,
                        prediction_data=suggestion["next_day_prediction"],
                        base_close_price=float(latest_price),
                        ai_provider=suggestion.get("ai_provider", "Unknown")
                    )
                    success += 1
                    provider = suggestion.get("ai_provider", "?")
                    print(f"  OK (base={latest_price}, provider={provider})", flush=True)
                else:
                    print(f"  SKIP: AI 未回傳預測資料", flush=True)
                    skipped += 1

                # API 速率控制：每 3 支暫停 2 秒
                if i % 3 == 0 and i < len(to_generate):
                    time.sleep(2)

            except Exception as e:
                print(f"  FAIL: {e}", flush=True)
                failed += 1
                continue

        # 最終統計
        final_count = db.query(PredictionRecord).filter(
            PredictionRecord.prediction_date == today
        ).count()
        total_watchlist = len(unique_items)

        print(f"\n{'=' * 50}")
        print(f"結果: {success} 成功 / {skipped} 跳過 / {failed} 失敗")
        print(f"今日預測: {final_count}/{total_watchlist}")
        if final_count < total_watchlist:
            missing = set(s.stock_id for _, s, _ in unique_items) - set(
                r.stock_id for r in db.query(PredictionRecord.stock_id).filter(
                    PredictionRecord.prediction_date == today
                ).all()
            )
            print(f"缺少: {missing}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
