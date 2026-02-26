"""手動觸發為所有自選股生成 AI 預測（讀取 .env 設定）"""
from app.database import SessionLocal
from app.models import Watchlist, Stock, User
from app.services.prediction_tracker import PredictionTracker
from app.services.ai_suggestion_service import AISuggestionService

def main():
    db = SessionLocal()
    prediction_tracker = PredictionTracker()

    try:
        watchlist_items = db.query(Watchlist, Stock, User).join(
            Stock, Watchlist.stock_id == Stock.stock_id
        ).join(
            User, Watchlist.user_id == User.id
        ).all()

        print(f"找到 {len(watchlist_items)} 支自選股需要生成預測")

        processed = set()
        success = 0
        for wl, stock, user in watchlist_items:
            key = f"{stock.stock_id}_{stock.market_region}"
            if key in processed:
                continue
            processed.add(key)

            try:
                market = stock.market_region or "TW"
                print(f"\n生成預測: {stock.stock_id} {stock.name} ({market})...", flush=True)
                service = AISuggestionService.for_user(user)
                suggestion = service.generate_suggestion(stock.stock_id, stock.name, market=market)

                if suggestion and suggestion.get("next_day_prediction"):
                    prediction_tracker.save_prediction(
                        db=db,
                        stock_id=stock.stock_id,
                        stock_name=stock.name,
                        market=market,
                        prediction_data=suggestion["next_day_prediction"],
                        base_close_price=suggestion.get("analysis_scores", {}).get("latest_price", 0) or 0,
                        ai_provider=suggestion.get("ai_provider", "Unknown")
                    )
                    success += 1
                    print(f"  ✓ 完成", flush=True)
                else:
                    print(f"  ✗ 無預測資料", flush=True)
            except Exception as e:
                print(f"  ✗ 錯誤: {e}", flush=True)
                continue

        print(f"\n{'='*40}")
        print(f"完成！成功生成 {success}/{len(processed)} 支股票的預測")
    finally:
        db.close()

if __name__ == "__main__":
    main()
