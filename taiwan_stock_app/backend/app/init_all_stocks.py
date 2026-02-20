"""
初始化完整台股資料庫腳本
使用 FinMind API 獲取所有台股上市、上櫃股票
"""
import sys
import os
import logging

from app.database import SessionLocal, engine, Base
from app.models import Stock
from app.data_fetchers import FinMindFetcher
from app.config import settings

logger = logging.getLogger(__name__)

# 創建資料表
Base.metadata.create_all(bind=engine)

def init_all_stocks():
    """初始化所有台股資料"""
    db = SessionLocal()
    finmind = FinMindFetcher(settings.FINMIND_TOKEN)

    try:
        logger.info("開始獲取台股列表...")

        # 獲取台股上市股票列表
        logger.info("正在獲取上市股票...")
        twse_stocks = finmind.get_stock_list()

        if twse_stocks is None or len(twse_stocks) == 0:
            logger.error("無法獲取股票列表，請檢查 FinMind API Token")
            return

        logger.info(f"獲取到 {len(twse_stocks)} 支股票")
        logger.info("開始寫入資料庫...")

        added_count = 0
        existing_count = 0
        error_count = 0

        for _, row in twse_stocks.iterrows():
            try:
                stock_id = row.get('stock_id', '')
                name = row.get('stock_name', '')
                industry = row.get('industry_category', '其他')
                market = row.get('type', 'TWSE')  # TWSE 上市, OTC 上櫃

                # 跳過無效資料
                if not stock_id or not name:
                    continue

                # 只保留數字股票代碼（排除指數、ETF等特殊代碼）
                if not stock_id.isdigit():
                    continue

                # 檢查是否已存在
                existing = db.query(Stock).filter(Stock.stock_id == stock_id).first()
                if existing:
                    existing_count += 1
                    if existing_count % 100 == 0:
                        logger.info(f"  處理中... 已存在 {existing_count} 筆")
                    continue

                # 新增股票
                stock = Stock(
                    stock_id=stock_id,
                    name=name,
                    industry=industry,
                    market=market
                )
                db.add(stock)
                db.flush()  # 立即flush檢查重複
                added_count += 1

                if added_count % 100 == 0:
                    db.commit()  # 每 100 筆提交一次
                    logger.info(f"  已新增 {added_count} 筆股票...")

            except Exception as e:
                error_count += 1
                if 'duplicate key' not in str(e).lower():
                    logger.warning(f"  處理 {stock_id} 時發生錯誤: {e}")
                db.rollback()
                continue

        # 最後一次提交
        db.commit()

        logger.info("=" * 60)
        logger.info(f"初始化完成！")
        logger.info(f"   新增股票：{added_count} 筆")
        logger.info(f"   已存在：{existing_count} 筆")
        logger.info(f"   錯誤：{error_count} 筆")
        logger.info(f"   總計：{added_count + existing_count} 筆股票在資料庫中")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"發生錯誤：{e}", exc_info=True)
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("台股完整資料庫初始化工具")
    logger.info("=" * 60)
    init_all_stocks()
