"""
初始化股票資料庫腳本
添加常見台股到資料庫
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, engine
from app.models import Stock, Base

# 創建資料表
Base.metadata.create_all(bind=engine)

# 常見台股列表
STOCKS = [
    # 半導體
    ("2330", "台積電", "半導體業", "TWSE"),
    ("2303", "聯電", "半導體業", "TWSE"),
    ("2454", "聯發科", "半導體業", "TWSE"),
    ("2408", "南亞科", "半導體業", "TWSE"),
    ("3034", "聯詠", "半導體業", "TWSE"),

    # 電子
    ("2317", "鴻海", "電腦及週邊設備業", "TWSE"),
    ("2382", "廣達", "電腦及週邊設備業", "TWSE"),
    ("2308", "台達電", "電子零組件業", "TWSE"),
    ("2357", "華碩", "電腦及週邊設備業", "TWSE"),
    ("2395", "研華", "電腦及週邊設備業", "TWSE"),

    # 金融
    ("2882", "國泰金", "金融保險業", "TWSE"),
    ("2881", "富邦金", "金融保險業", "TWSE"),
    ("2886", "兆豐金", "金融保險業", "TWSE"),
    ("2891", "中信金", "金融保險業", "TWSE"),
    ("2892", "第一金", "金融保險業", "TWSE"),
    ("2884", "玉山金", "金融保險業", "TWSE"),

    # 傳產
    ("2002", "中鋼", "鋼鐵工業", "TWSE"),
    ("1301", "台塑", "塑膠工業", "TWSE"),
    ("1303", "南亞", "塑膠工業", "TWSE"),
    ("1326", "台化", "塑膠工業", "TWSE"),

    # 通信
    ("2412", "中華電", "通信網路業", "TWSE"),
    ("4904", "遠傳", "通信網路業", "TWSE"),
    ("3045", "台灣大", "通信網路業", "TWSE"),

    # 航運
    ("2603", "長榮", "航運業", "TWSE"),
    ("2609", "陽明", "航運業", "TWSE"),
    ("2615", "萬海", "航運業", "TWSE"),

    # 食品
    ("1216", "統一", "食品工業", "TWSE"),
    ("1301", "台塑", "塑膠工業", "TWSE"),

    # 其他
    ("2412", "中華電", "通信網路業", "TWSE"),
    ("9904", "寶成", "其他", "TWSE"),
]

def init_stocks():
    """初始化股票資料"""
    db = SessionLocal()

    try:
        print("開始初始化股票資料...")
        added_count = 0
        existing_count = 0

        for stock_id, name, industry, market in STOCKS:
            # 檢查是否已存在
            existing = db.query(Stock).filter(Stock.stock_id == stock_id).first()
            if existing:
                existing_count += 1
                print(f"  [跳過] {stock_id} {name} (已存在)")
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
            print(f"  [新增] {stock_id} {name}")

        db.commit()

        print("\n" + "="*50)
        print(f"初始化完成！")
        print(f"新增股票：{added_count} 筆")
        print(f"已存在：{existing_count} 筆")
        print(f"總計：{added_count + existing_count} 筆")
        print("="*50)

    except Exception as e:
        print(f"錯誤：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_stocks()
