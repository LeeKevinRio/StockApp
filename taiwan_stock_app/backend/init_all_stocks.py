"""
初始化完整台股資料庫腳本
使用 FinMind API 獲取所有台股上市、上櫃股票
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app.models import Stock, Base
from app.data_fetchers import FinMindFetcher
from app.config import settings

# 創建資料表
Base.metadata.create_all(bind=engine)

def init_all_stocks():
    """初始化所有台股資料"""
    db = SessionLocal()
    finmind = FinMindFetcher(settings.FINMIND_TOKEN)

    try:
        print("開始獲取台股列表...")

        # 獲取台股上市股票列表
        print("\n正在獲取上市股票...")
        twse_stocks = finmind.get_stock_list()

        if twse_stocks is None or len(twse_stocks) == 0:
            print("❌ 無法獲取股票列表，請檢查 FinMind API Token")
            return

        print(f"✅ 獲取到 {len(twse_stocks)} 支股票")
        print("\n開始寫入資料庫...")

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
                        print(f"  處理中... 已存在 {existing_count} 筆")
                    continue

                # 新增股票
                stock = Stock(
                    stock_id=stock_id,
                    name=name,
                    industry=industry,
                    market=market
                )
                db.add(stock)
                added_count += 1

                if added_count % 100 == 0:
                    db.commit()  # 每 100 筆提交一次
                    print(f"  ✅ 已新增 {added_count} 筆股票...")

            except Exception as e:
                error_count += 1
                print(f"  ⚠️  處理 {stock_id} 時發生錯誤: {e}")
                continue

        # 最後一次提交
        db.commit()

        print("\n" + "="*60)
        print(f"✅ 初始化完成！")
        print(f"   新增股票：{added_count} 筆")
        print(f"   已存在：{existing_count} 筆")
        print(f"   錯誤：{error_count} 筆")
        print(f"   總計：{added_count + existing_count} 筆股票在資料庫中")
        print("="*60)

    except Exception as e:
        print(f"❌ 發生錯誤：{e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("台股完整資料庫初始化工具")
    print("="*60)
    init_all_stocks()
