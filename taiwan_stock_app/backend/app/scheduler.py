"""
Scheduler - 定時任務排程器
- 台股收盤後 3 小時更新預測 (16:30)
- 美股收盤後 3 小時更新預測 (07:00 台灣時間)
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import pytz

from app.database import SessionLocal
from app.services.prediction_tracker import PredictionTracker
from app.services.ai_suggestion_service import AISuggestionService
from app.models import Watchlist, Stock, User

# 台灣時區
TW_TZ = pytz.timezone('Asia/Taipei')

scheduler = BackgroundScheduler(timezone=TW_TZ)
prediction_tracker = PredictionTracker()


def update_tw_predictions():
    """
    更新台股預測的實際結果
    排程：每個交易日 16:30（收盤後3小時）
    """
    print(f"[{datetime.now(TW_TZ)}] Starting TW prediction update...")
    db = SessionLocal()
    try:
        updated = prediction_tracker.update_actual_results(db, market="TW")
        print(f"[{datetime.now(TW_TZ)}] Updated {updated} TW prediction records")
    except Exception as e:
        print(f"[{datetime.now(TW_TZ)}] TW prediction update error: {e}")
    finally:
        db.close()


def update_us_predictions():
    """
    更新美股預測的實際結果
    排程：每個交易日 07:00（美股收盤後約3小時，台灣時間）
    """
    print(f"[{datetime.now(TW_TZ)}] Starting US prediction update...")
    db = SessionLocal()
    try:
        updated = prediction_tracker.update_actual_results(db, market="US")
        print(f"[{datetime.now(TW_TZ)}] Updated {updated} US prediction records")
    except Exception as e:
        print(f"[{datetime.now(TW_TZ)}] US prediction update error: {e}")
    finally:
        db.close()


def generate_daily_predictions():
    """
    為所有用戶的自選股生成新的每日預測
    排程：台股 09:30（開盤後），美股 22:00（開盤後，台灣時間）
    """
    print(f"[{datetime.now(TW_TZ)}] Starting daily prediction generation...")
    db = SessionLocal()
    try:
        # 獲取所有用戶的自選股
        watchlist_items = db.query(Watchlist, Stock, User).join(
            Stock, Watchlist.stock_id == Stock.stock_id
        ).join(
            User, Watchlist.user_id == User.id
        ).all()

        processed = set()
        for wl, stock, user in watchlist_items:
            # 避免重複處理同一股票
            key = f"{stock.stock_id}_{stock.market_region}"
            if key in processed:
                continue
            processed.add(key)

            try:
                market = stock.market_region or "TW"
                service = AISuggestionService.for_user(user)
                suggestion = service.generate_suggestion(stock.stock_id, stock.name, market=market)

                # 儲存預測記錄
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
                    print(f"Generated prediction for {stock.stock_id}")
            except Exception as e:
                print(f"Error generating prediction for {stock.stock_id}: {e}")
                continue

        print(f"[{datetime.now(TW_TZ)}] Generated predictions for {len(processed)} stocks")
    except Exception as e:
        print(f"[{datetime.now(TW_TZ)}] Daily prediction generation error: {e}")
    finally:
        db.close()


def start_scheduler():
    """啟動排程器"""
    # 台股：每週一至週五 16:30 更新實際結果
    scheduler.add_job(
        update_tw_predictions,
        CronTrigger(day_of_week='mon-fri', hour=16, minute=30, timezone=TW_TZ),
        id='update_tw_predictions',
        replace_existing=True
    )

    # 美股：每週二至週六 07:00 更新實際結果（美股週一至週五收盤）
    scheduler.add_job(
        update_us_predictions,
        CronTrigger(day_of_week='tue-sat', hour=7, minute=0, timezone=TW_TZ),
        id='update_us_predictions',
        replace_existing=True
    )

    # 可選：自動生成每日預測
    # 台股：每週一至週五 09:30
    # scheduler.add_job(
    #     generate_daily_predictions,
    #     CronTrigger(day_of_week='mon-fri', hour=9, minute=30, timezone=TW_TZ),
    #     id='generate_tw_predictions',
    #     replace_existing=True
    # )

    scheduler.start()
    print(f"[{datetime.now(TW_TZ)}] Scheduler started with jobs:")
    for job in scheduler.get_jobs():
        print(f"  - {job.id}: {job.trigger}")


def stop_scheduler():
    """停止排程器"""
    scheduler.shutdown()
    print("Scheduler stopped")
