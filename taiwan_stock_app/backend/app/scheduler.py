"""
Scheduler - 定時任務排程器
- 台股收盤後 3 小時更新預測 (16:30)
- 美股收盤後 3 小時更新預測 (07:00 台灣時間)
- 新聞抓取：交易時段每 30 分鐘
- 社群抓取：每 2 小時（09:00-22:00）
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import asyncio
import logging
import pytz

from app.database import SessionLocal
from app.services.prediction_tracker import PredictionTracker
from app.services.ai_suggestion_service import AISuggestionService
from app.models import Watchlist, Stock, User

logger = logging.getLogger(__name__)

# 台灣時區
TW_TZ = pytz.timezone('Asia/Taipei')

scheduler = BackgroundScheduler(timezone=TW_TZ)
prediction_tracker = PredictionTracker()


def update_tw_predictions():
    """
    更新台股預測的實際結果
    排程：每個交易日 16:30（收盤後3小時）
    """
    logger.info("Starting TW prediction update...")
    db = SessionLocal()
    try:
        updated = prediction_tracker.update_actual_results(db, market="TW")
        logger.info("Updated %d TW prediction records", updated)
    except Exception as e:
        logger.error("TW prediction update error: %s", e)
    finally:
        db.close()


def update_us_predictions():
    """
    更新美股預測的實際結果
    排程：每個交易日 07:00（美股收盤後約3小時，台灣時間）
    """
    logger.info("Starting US prediction update...")
    db = SessionLocal()
    try:
        updated = prediction_tracker.update_actual_results(db, market="US")
        logger.info("Updated %d US prediction records", updated)
    except Exception as e:
        logger.error("US prediction update error: %s", e)
    finally:
        db.close()


def generate_daily_predictions():
    """
    為所有用戶的自選股生成新的每日預測
    排程：台股 09:30（開盤後），美股 22:00（開盤後，台灣時間）
    """
    logger.info("Starting daily prediction generation...")
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
                    logger.info("Generated prediction for %s", stock.stock_id)
            except Exception as e:
                logger.error("Error generating prediction for %s: %s", stock.stock_id, e)
                continue

        logger.info("Generated predictions for %d stocks", len(processed))
    except Exception as e:
        logger.error("Daily prediction generation error: %s", e)
    finally:
        db.close()


def fetch_market_news_task():
    """
    排程抓取市場新聞
    交易時段每 30 分鐘抓取熱門股票新聞
    """
    logger.info("Starting market news fetch...")
    db = SessionLocal()
    try:
        from app.services.news_service import news_service

        # 抓取自選股中的熱門股票新聞
        watchlist_stocks = db.query(Watchlist.stock_id).distinct().limit(20).all()
        stock_ids = [w[0] for w in watchlist_stocks]

        if not stock_ids:
            stock_ids = ['2330', '2317', '2454', '2308', '2881']  # 預設熱門台股

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        fetched_count = 0
        for stock_id in stock_ids:
            try:
                loop.run_until_complete(
                    news_service.get_stock_news(db, stock_id, limit=5, use_cache=False)
                )
                fetched_count += 1
            except Exception as e:
                logger.warning("新聞抓取失敗 %s: %s", stock_id, e)

        loop.close()
        logger.info("Fetched news for %d/%d stocks", fetched_count, len(stock_ids))
    except Exception as e:
        logger.error("Market news fetch error: %s", e)
    finally:
        db.close()


def fetch_social_data_task():
    """
    排程抓取社群數據
    每 2 小時抓取一次（09:00-22:00）
    """
    logger.info("Starting social data fetch...")
    db = SessionLocal()
    try:
        from app.services.sentiment_service import sentiment_service

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 抓取熱門討論股票
        loop.run_until_complete(sentiment_service.get_hot_stocks(db, limit=20))

        # 抓取自選股的社群數據
        watchlist_stocks = db.query(Watchlist.stock_id).distinct().limit(10).all()
        for (stock_id,) in watchlist_stocks:
            try:
                loop.run_until_complete(
                    sentiment_service.get_stock_sentiment(db, stock_id)
                )
            except Exception as e:
                logger.warning("社群數據抓取失敗 %s: %s", stock_id, e)

        loop.close()
        logger.info("Social data fetch completed")
    except Exception as e:
        logger.error("Social data fetch error: %s", e)
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

    # 每日自動生成 AI 預測
    # 台股：每週一至週五 09:30（開盤後）
    scheduler.add_job(
        generate_daily_predictions,
        CronTrigger(day_of_week='mon-fri', hour=9, minute=30, timezone=TW_TZ),
        id='generate_tw_predictions',
        replace_existing=True
    )

    # 新聞抓取：每週一至週五，09:00-16:00 每 30 分鐘
    scheduler.add_job(
        fetch_market_news_task,
        CronTrigger(day_of_week='mon-fri', hour='9-16', minute='0,30', timezone=TW_TZ),
        id='fetch_market_news',
        replace_existing=True
    )

    # 社群數據抓取：每天 09:00-22:00 每 2 小時
    scheduler.add_job(
        fetch_social_data_task,
        CronTrigger(hour='9,11,13,15,17,19,21', minute=0, timezone=TW_TZ),
        id='fetch_social_data',
        replace_existing=True
    )

    scheduler.start()
    logger.info("Scheduler started with jobs:")
    for job in scheduler.get_jobs():
        logger.info("  - %s: %s", job.id, job.trigger)


def stop_scheduler():
    """停止排程器"""
    scheduler.shutdown()
    logger.info("Scheduler stopped")
