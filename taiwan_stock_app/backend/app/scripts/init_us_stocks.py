"""
初始化熱門美股資料到資料庫
Initialize popular US stocks in the database
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models.stock import Stock, Base
from app.data_fetchers.us_stock_fetcher import USStockFetcher

logger = logging.getLogger(__name__)

# Popular US stocks to initialize
POPULAR_US_STOCKS = [
    # Technology
    "AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "NVDA", "TSLA",
    "AMD", "INTC", "CRM", "ORCL", "ADBE", "NFLX", "PYPL",
    # Finance
    "JPM", "BAC", "WFC", "GS", "MS", "V", "MA", "AXP",
    # Healthcare
    "JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY",
    # Consumer
    "WMT", "HD", "MCD", "NKE", "SBUX", "KO", "PEP",
    # Energy
    "XOM", "CVX",
    # Industrial
    "BA", "CAT", "GE",
    # ETFs
    "SPY", "QQQ", "DIA", "IWM", "VTI",
]


def init_us_stocks():
    """Initialize popular US stocks in database"""
    fetcher = USStockFetcher()
    db: Session = SessionLocal()

    try:
        added_count = 0
        updated_count = 0
        failed_count = 0

        for symbol in POPULAR_US_STOCKS:
            try:
                # Check if stock already exists
                existing = db.query(Stock).filter(
                    Stock.stock_id == symbol,
                    Stock.market_region == 'US'
                ).first()

                # Get stock info from yfinance
                info = fetcher.get_stock_info(symbol)

                if info:
                    if existing:
                        # Update existing stock
                        existing.name = info.get('name', symbol)
                        existing.industry = info.get('industry')
                        existing.sector = info.get('sector')
                        existing.market = info.get('exchange')
                        updated_count += 1
                        logger.info(f"Updated: {symbol} - {info.get('name', symbol)}")
                    else:
                        # Create new stock
                        new_stock = Stock(
                            stock_id=symbol,
                            name=info.get('name', symbol),
                            market=info.get('exchange'),
                            industry=info.get('industry'),
                            market_region='US',
                            sector=info.get('sector'),
                        )
                        db.add(new_stock)
                        added_count += 1
                        logger.info(f"Added: {symbol} - {info.get('name', symbol)}")
                else:
                    logger.warning(f"No info found for {symbol}")
                    failed_count += 1

            except Exception as e:
                logger.error(f"Error processing {symbol}: {e}")
                failed_count += 1
                continue

        db.commit()
        logger.info(f"=== Summary ===")
        logger.info(f"Added: {added_count}")
        logger.info(f"Updated: {updated_count}")
        logger.info(f"Failed: {failed_count}")
        logger.info(f"Total: {len(POPULAR_US_STOCKS)}")

    except Exception as e:
        logger.error(f"Database error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Initializing popular US stocks...")
    logger.info("=" * 50)
    init_us_stocks()
    logger.info("=" * 50)
    logger.info("Done!")
