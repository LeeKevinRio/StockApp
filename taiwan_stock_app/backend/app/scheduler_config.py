"""
APScheduler 配置與初始化
用於每日盤前摘要排程
"""

import logging
from datetime import timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import asyncio

logger = logging.getLogger(__name__)

# 台灣時區 (UTC+8)
TW_TIMEZONE = timezone(timedelta(hours=8))


def create_scheduler():
    """
    創建並配置 APScheduler 實例

    Returns:
        BackgroundScheduler: 配置好的排程器
    """
    scheduler = BackgroundScheduler()

    # 設置排程器日誌
    logging.getLogger('apscheduler.schedulers.background').setLevel(logging.WARNING)
    logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)

    return scheduler


def add_daily_summary_job(scheduler: BackgroundScheduler, hour: int = 8, minute: int = 0):
    """
    新增每日盤前摘要排程任務

    Args:
        scheduler: APScheduler 實例
        hour: 執行時間 (小時, 0-23)
        minute: 執行時間 (分鐘, 0-59)
    """
    from app.services.daily_summary_service import daily_summary_service

    def run_daily_summary():
        """包裝函數，用於適配 APScheduler 的同步調用"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(daily_summary_service.schedule_daily_summary())
        except Exception as e:
            logger.error(f"每日摘要任務執行失敗: {e}")
        finally:
            loop.close()

    # 每天指定時間執行
    scheduler.add_job(
        run_daily_summary,
        trigger=CronTrigger(
            hour=hour,
            minute=minute,
            second=0,
            timezone=TW_TIMEZONE
        ),
        id='daily_summary',
        name='每日盤前摘要 (台灣時間 8:00 AM)',
        replace_existing=True,
        misfire_grace_time=600  # 最多容許 10 分鐘遲到
    )

    logger.info(f"已新增每日摘要任務 - 每天 {hour:02d}:{minute:02d} (台灣時間)")


def add_test_job(scheduler: BackgroundScheduler):
    """
    新增測試用排程任務 (每 5 分鐘執行一次)
    僅供開發測試，生產環境應移除

    Args:
        scheduler: APScheduler 實例
    """
    from app.services.daily_summary_service import daily_summary_service

    def run_test_task():
        """測試任務"""
        logger.info("執行測試摘要任務...")
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(daily_summary_service.generate_summary())
            logger.info("測試摘要任務完成")
        except Exception as e:
            logger.error(f"測試任務失敗: {e}")
        finally:
            loop.close()

    scheduler.add_job(
        run_test_task,
        trigger='interval',
        minutes=5,
        id='test_summary',
        name='測試摘要任務',
        replace_existing=True
    )

    logger.info("已新增測試任務 - 每 5 分鐘執行一次")


def initialize_scheduler(app, enable_daily_summary: bool = True,
                        enable_test_job: bool = False,
                        daily_summary_hour: int = 8,
                        daily_summary_minute: int = 0):
    """
    初始化排程器並掛載到 FastAPI 應用

    Args:
        app: FastAPI 應用實例
        enable_daily_summary: 是否啟用每日摘要任務
        enable_test_job: 是否啟用測試任務 (開發用)
        daily_summary_hour: 每日摘要執行時間 (小時)
        daily_summary_minute: 每日摘要執行時間 (分鐘)

    Example:
        ```python
        from fastapi import FastAPI
        from app.scheduler_config import initialize_scheduler

        app = FastAPI()
        initialize_scheduler(app)
        ```
    """

    scheduler = create_scheduler()

    # 新增排程任務
    if enable_daily_summary:
        add_daily_summary_job(scheduler, hour=daily_summary_hour, minute=daily_summary_minute)

    if enable_test_job:
        logger.warning("⚠️ 測試任務已啟用，生產環境應禁用")
        add_test_job(scheduler)

    # 啟動事件
    @app.on_event("startup")
    async def startup_event():
        """應用啟動時啟動排程器"""
        scheduler.start()
        logger.info("✅ APScheduler 已啟動")

        # 列出所有任務
        jobs = scheduler.get_jobs()
        if jobs:
            logger.info(f"已有 {len(jobs)} 個排程任務:")
            for job in jobs:
                logger.info(f"  - {job.name} (ID: {job.id})")
        else:
            logger.warning("未發現任何排程任務")

    # 關閉事件
    @app.on_event("shutdown")
    async def shutdown_event():
        """應用關閉時關閉排程器"""
        scheduler.shutdown()
        logger.info("✅ APScheduler 已關閉")

    return scheduler


# 快速初始化函數 (用於簡單情況)
class SchedulerManager:
    """排程器管理類"""

    _instance = None

    def __init__(self):
        self.scheduler = create_scheduler()
        self.is_running = False

    @classmethod
    def get_instance(cls):
        """取得單例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def add_daily_summary(self, hour: int = 8, minute: int = 0):
        """新增每日摘要任務"""
        if not self.is_running:
            add_daily_summary_job(self.scheduler, hour=hour, minute=minute)
        else:
            logger.warning("排程器已執行，無法動態新增任務，請在啟動前新增")

    def add_test_job(self):
        """新增測試任務"""
        if not self.is_running:
            add_test_job(self.scheduler)
        else:
            logger.warning("排程器已執行，無法動態新增任務，請在啟動前新增")

    def start(self):
        """啟動排程器"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("排程器已啟動")
        else:
            logger.warning("排程器已在執行中")

    def stop(self):
        """停止排程器"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("排程器已停止")

    def get_jobs(self):
        """取得所有排程任務"""
        return self.scheduler.get_jobs()

    def remove_job(self, job_id: str):
        """移除指定的排程任務"""
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"任務 {job_id} 已移除")
        except Exception as e:
            logger.error(f"移除任務 {job_id} 失敗: {e}")


# 範例用法
if __name__ == "__main__":
    """
    測試排程器配置
    運行: python app/config/scheduler_config.py
    """
    import time

    # 建立排程器
    manager = SchedulerManager.get_instance()

    # 新增任務
    manager.add_daily_summary(hour=8, minute=0)
    manager.add_test_job()

    # 啟動
    manager.start()

    # 列出任務
    print("\n已新增的排程任務:")
    for job in manager.get_jobs():
        print(f"  - {job.name} (下次執行: {job.next_run_time})")

    # 運行 30 秒以查看測試任務執行
    print("\n排程器已啟動，運行 30 秒...")
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()
