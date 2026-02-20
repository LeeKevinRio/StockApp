"""
匯入台灣全部上市櫃股票清單
"""
import requests
import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.database import SessionLocal, create_tables
from app.models import Stock

logger = logging.getLogger(__name__)


def fetch_twse_stocks():
    """取得上市股票清單"""
    url = "https://www.twse.com.tw/rwd/zh/afterTrading/BWIBBU_d?response=json"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        stocks = []
        for row in data.get("data", []):
            if len(row) >= 2:
                stock_id = row[0].strip()
                name = row[1].strip()
                # 只取純數字的股票代號（排除權證、ETN等）
                if stock_id.isdigit() and len(stock_id) == 4:
                    stocks.append({
                        "stock_id": stock_id,
                        "name": name,
                        "market": "TWSE"
                    })
        return stocks
    except Exception as e:
        logger.error(f"取得上市股票清單失敗: {e}")
        return []


def fetch_tpex_stocks():
    """取得上櫃股票清單"""
    url = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()

        stocks = []
        for item in data:
            stock_id = item.get("SecuritiesCompanyCode", "").strip()
            name = item.get("CompanyName", "").strip()
            # 只取純數字的股票代號
            if stock_id.isdigit() and len(stock_id) == 4:
                stocks.append({
                    "stock_id": stock_id,
                    "name": name,
                    "market": "TPEx"
                })
        return stocks
    except Exception as e:
        logger.error(f"取得上櫃股票清單失敗: {e}")
        return []


def fetch_all_stocks_alternative():
    """備用方案：從證交所股票列表取得"""
    stocks = []

    # 上市股票
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=2"
        response = requests.get(url, timeout=30)
        response.encoding = 'big5'

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 5:
                first_cell = cells[0].get_text().strip()
                if '\u3000' in first_cell:
                    parts = first_cell.split('\u3000')
                    if len(parts) == 2:
                        stock_id = parts[0].strip()
                        name = parts[1].strip()
                        market_type = cells[3].get_text().strip()
                        if stock_id.isdigit() and len(stock_id) == 4 and market_type == "股票":
                            stocks.append({
                                "stock_id": stock_id,
                                "name": name,
                                "market": "TWSE"
                            })
    except Exception as e:
        logger.error(f"備用方案（上市）失敗: {e}")

    # 上櫃股票
    try:
        url = "https://isin.twse.com.tw/isin/C_public.jsp?strMode=4"
        response = requests.get(url, timeout=30)
        response.encoding = 'big5'

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')

        for row in soup.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) >= 5:
                first_cell = cells[0].get_text().strip()
                if '\u3000' in first_cell:
                    parts = first_cell.split('\u3000')
                    if len(parts) == 2:
                        stock_id = parts[0].strip()
                        name = parts[1].strip()
                        market_type = cells[3].get_text().strip()
                        if stock_id.isdigit() and len(stock_id) == 4 and market_type == "股票":
                            stocks.append({
                                "stock_id": stock_id,
                                "name": name,
                                "market": "TPEx"
                            })
    except Exception as e:
        logger.error(f"備用方案（上櫃）失敗: {e}")

    return stocks


def import_stocks():
    """匯入股票到資料庫"""
    # 確保資料表存在
    create_tables()

    db = SessionLocal()

    try:
        # 取得所有股票
        logger.info("正在取得上市股票清單...")
        twse_stocks = fetch_twse_stocks()
        logger.info(f"取得 {len(twse_stocks)} 檔上市股票")

        logger.info("正在取得上櫃股票清單...")
        tpex_stocks = fetch_tpex_stocks()
        logger.info(f"取得 {len(tpex_stocks)} 檔上櫃股票")

        all_stocks = twse_stocks + tpex_stocks

        # 如果主要方案失敗，使用備用方案
        if len(all_stocks) < 100:
            logger.info("使用備用方案取得股票清單...")
            all_stocks = fetch_all_stocks_alternative()
            logger.info(f"備用方案取得 {len(all_stocks)} 檔股票")

        # 匯入到資料庫
        imported = 0
        updated = 0

        for stock_data in all_stocks:
            existing = db.query(Stock).filter(Stock.stock_id == stock_data["stock_id"]).first()

            if existing:
                existing.name = stock_data["name"]
                existing.market = stock_data["market"]
                updated += 1
            else:
                stock = Stock(
                    stock_id=stock_data["stock_id"],
                    name=stock_data["name"],
                    market=stock_data["market"]
                )
                db.add(stock)
                imported += 1

        db.commit()
        logger.info(f"匯入完成！新增 {imported} 檔，更新 {updated} 檔")
        logger.info(f"資料庫共有 {db.query(Stock).count()} 檔股票")

    except Exception as e:
        db.rollback()
        logger.error(f"匯入失敗: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import_stocks()
