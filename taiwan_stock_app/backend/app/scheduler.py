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
from datetime import datetime, date
import asyncio
import logging
import pytz

from app.database import SessionLocal
from app.services.prediction_tracker import PredictionTracker
from app.services.ai_suggestion_service import AISuggestionService
from app.services.trading_calendar import is_trading_day
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
    台股休市日（國定假日）跳過，避免無謂查詢與 log 噪音。
    """
    today = date.today()
    if not is_trading_day(today, market="TW"):
        logger.info("Skip TW prediction update: %s 為台股休市日", today)
        return
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
    對應的美股交易日為 _TW 時區的「昨天」，需以美東日期判斷。
    """
    # 07:00 TW ≈ 18:00 (前一日) ET，對應的美股交易日是「TW 昨天」
    from datetime import timedelta
    us_business_day = date.today() - timedelta(days=1)
    if not is_trading_day(us_business_day, market="US"):
        logger.info("Skip US prediction update: %s 為美股休市日", us_business_day)
        return
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
    台股休市日跳過台股部分；美股交易日獨立判斷。
    """
    today = date.today()
    tw_open = is_trading_day(today, market="TW")
    if not tw_open:
        logger.info("%s 為台股休市日，將僅處理美股自選股", today)
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
                # 該市場休市時跳過此股，避免浪費 AI 配額
                if not is_trading_day(today, market=market):
                    continue
                # 傳入 db 讓 generate_suggestion 內部能讀到歷史準確率回饋，
                # 自動依過往幅度偏差調整新預測（少了 db 此校正會永遠跳過）
                service = AISuggestionService.for_user(user, db=db)
                suggestion = service.generate_suggestion(stock.stock_id, stock.name, market=market, db=db)

                # 儲存預測記錄
                if suggestion and suggestion.get("next_day_prediction"):
                    latest_price = suggestion.get("analysis_scores", {}).get("latest_price")
                    if not latest_price or float(latest_price) <= 0:
                        logger.warning("跳過 %s 預測：無有效價格資料 (latest_price=%s)", stock.stock_id, latest_price)
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
                    logger.info("Generated prediction for %s (base_price=%.2f)", stock.stock_id, float(latest_price))
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
    台股休市日跳過（國際/美股新聞另由 fetch_social_data_task 涵蓋部分）
    """
    if not is_trading_day(date.today(), market="TW"):
        logger.info("Skip market news fetch: 台股休市日")
        return
    logger.info("Starting market news fetch...")
    db = SessionLocal()
    try:
        from app.services.news_service import news_service

        # 抓取自選股中的熱門股票新聞（含市場資訊以路由 TW/US 不同來源）
        watchlist_stocks = db.query(Watchlist, Stock).join(
            Stock, Watchlist.stock_id == Stock.stock_id
        ).distinct().limit(20).all()
        stock_market_pairs = [
            (s.stock_id, s.market_region or "TW") for _, s in watchlist_stocks
        ]

        if not stock_market_pairs:
            stock_market_pairs = [
                ('2330', 'TW'), ('2317', 'TW'), ('2454', 'TW'),
                ('2308', 'TW'), ('2881', 'TW'),
            ]

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def _fetch_all_news():
            """並行抓取多支股票新聞，依市場走 TW / US 路徑"""
            tasks = [
                news_service.get_stock_news(db, sid, limit=5, use_cache=False, market=mkt)
                for sid, mkt in stock_market_pairs
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            count = 0
            for (sid, _mkt), result in zip(stock_market_pairs, results):
                if isinstance(result, Exception):
                    logger.warning("新聞抓取失敗 %s: %s", sid, result)
                else:
                    count += 1
            return count

        fetched_count = loop.run_until_complete(_fetch_all_news())
        loop.close()
        logger.info("Fetched news for %d/%d stocks", fetched_count, len(stock_market_pairs))
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

        async def _fetch_all_social():
            """並行抓取社群數據"""
            # 先抓取熱門討論股票
            await sentiment_service.get_hot_stocks(db, limit=20)
            # 再並行抓取自選股的社群數據
            watchlist_stocks = db.query(Watchlist.stock_id).distinct().limit(10).all()
            tasks = [
                sentiment_service.get_stock_sentiment(db, sid)
                for (sid,) in watchlist_stocks
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for (sid,), result in zip(watchlist_stocks, results):
                if isinstance(result, Exception):
                    logger.warning("社群數據抓取失敗 %s: %s", sid, result)

        loop.run_until_complete(_fetch_all_social())
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
