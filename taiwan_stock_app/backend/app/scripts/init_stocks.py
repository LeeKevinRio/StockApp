"""
初始化台股清單腳本
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal, engine
from app.models import Base, Stock
from app.data_fetchers import FinMindFetcher
from app.config import settings


def init_stocks():
    """從 FinMind 匯入台股清單"""
    print("正在初始化資料庫表格...")
    Base.metadata.create_all(bind=engine)

    print(f"正在從 FinMind 取得股票清單 (Token: {settings.FINMIND_TOKEN[:10]}...)...")

    fetcher = FinMindFetcher(settings.FINMIND_TOKEN)

    try:
        df = fetcher.get_stock_list()
        print(f"取得 {len(df)} 筆股票資料")
    except Exception as e:
        print(f"錯誤：無法從 FinMind 取得資料 - {e}")
        print("\n請確認：")
        print("1. FINMIND_TOKEN 是否正確設定在 .env 檔案")
        print("2. 可到 https://finmindtrade.com/ 免費註冊取得 Token")
        return

    db = SessionLocal()

    try:
        # 過濾只要股票（排除 ETF、權證等）
        # industry 欄位有值的通常是一般股票
        stocks_df = df[df['type'] == 'stock'] if 'type' in df.columns else df

        count = 0
        for _, row in stocks_df.iterrows():
            stock_id = str(row.get('stock_id', row.get('code', '')))

            # 跳過非一般股票代碼（如權證、ETF 特殊代碼）
            if not stock_id or len(stock_id) != 4 or not stock_id.isdigit():
                continue

            # 檢查是否已存在
            existing = db.query(Stock).filter(Stock.stock_id == stock_id).first()
            if existing:
                continue

            stock = Stock(
                stock_id=stock_id,
                name=row.get('stock_name', row.get('name', '')),
                industry=row.get('industry_category', row.get('industry', '')),
                market=row.get('type', 'twse'),
            )
            db.add(stock)
            count += 1

            if count % 100 == 0:
                print(f"已處理 {count} 筆...")
                db.commit()

        db.commit()
        print(f"\n✅ 成功匯入 {count} 筆股票資料！")

        # 顯示範例
        sample = db.query(Stock).limit(5).all()
        print("\n範例資料：")
        for s in sample:
            print(f"  {s.stock_id} - {s.name} ({s.industry})")

    except Exception as e:
        print(f"匯入失敗：{e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_stocks()
