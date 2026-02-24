"""
為所有自選股生成 AI 預測記錄
"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models import Watchlist, Stock, User
from app.services.ai_suggestion_service import AISuggestionService
from app.services.prediction_tracker import PredictionTracker

def generate_all_predictions():
    db = SessionLocal()
    tracker = PredictionTracker()

    try:
        # 獲取所有自選股
        watchlist_items = db.query(Watchlist, Stock, User).join(
            Stock, Watchlist.stock_id == Stock.stock_id
        ).join(
            User, Watchlist.user_id == User.id
        ).all()

        processed = set()
        success_count = 0

        for wl, stock, user in watchlist_items:
            # 避免重複處理
            if stock.stock_id in processed:
                continue
            processed.add(stock.stock_id)

            market = stock.market_region or "TW"
            print(f"\n處理 {stock.stock_id} {stock.name} ({market})...")

            try:
                # 生成 AI 建議
                service = AISuggestionService.for_user(user)
                suggestion = service.generate_suggestion(stock.stock_id, stock.name, market=market)

                if suggestion and suggestion.get("next_day_prediction"):
                    # 儲存預測記錄
                    analysis_scores = suggestion.get("analysis_scores", {})
                    latest_price = analysis_scores.get("latest_price", 0) or 0
                    ai_provider = suggestion.get("ai_provider", "Unknown")

                    tracker.save_prediction(
                        db=db,
                        stock_id=stock.stock_id,
                        stock_name=stock.name,
                        market=market,
                        prediction_data=suggestion["next_day_prediction"],
                        base_close_price=latest_price,
                        ai_provider=ai_provider
                    )

                    pred = suggestion["next_day_prediction"]
                    print(f"  [OK] prediction: {pred.get('direction')} {pred.get('predicted_change_percent')}%")
                    print(f"    AI: {ai_provider}")
                    success_count += 1
                else:
                    print(f"  [FAIL] no prediction generated")

            except Exception as e:
                print(f"  [ERR] {e}")
                continue

        print(f"\n完成！成功生成 {success_count}/{len(processed)} 筆預測記錄")

    finally:
        db.close()

if __name__ == "__main__":
    generate_all_predictions()
