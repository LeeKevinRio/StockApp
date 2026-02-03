"""Test US stock fetcher"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.data_fetchers.us_stock_fetcher import USStockFetcher

def main():
    fetcher = USStockFetcher()

    print("=== Testing search_stocks('AAPL') ===")
    try:
        results = fetcher.search_stocks('AAPL')
        print(f"Results count: {len(results)}")
        for r in results:
            print(f"  - {r}")
    except Exception as e:
        print(f"Error: {e}")

    print()
    print("=== Testing get_realtime_quote('AAPL') ===")
    try:
        quote = fetcher.get_realtime_quote('AAPL')
        if quote:
            print(f"Symbol: {quote.get('symbol')}")
            print(f"Name: {quote.get('name')}")
            print(f"Price: ${quote.get('price')}")
            print(f"Change: {quote.get('change')} ({quote.get('change_percent')}%)")
        else:
            print("No quote returned")
    except Exception as e:
        print(f"Error: {e}")

    print()
    print("=== Testing get_stock_info('MSFT') ===")
    try:
        info = fetcher.get_stock_info('MSFT')
        if info:
            print(f"Symbol: {info.get('symbol')}")
            print(f"Name: {info.get('name')}")
            print(f"Sector: {info.get('sector')}")
            print(f"Industry: {info.get('industry')}")
        else:
            print("No info returned")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
