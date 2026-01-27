"""Test news API for US stocks"""
import requests
import json

# Login
login_resp = requests.post('http://localhost:8001/api/auth/login', json={'email': 'test@test.com', 'password': 'test123'})
if login_resp.status_code != 200:
    print(f'Login failed: {login_resp.text}')
    exit(1)

token = login_resp.json()['access_token']
print(f'Token obtained: {token[:30]}...')

headers = {'Authorization': f'Bearer {token}'}

# Test US stock news
print('\n=== Testing US Stock News (AAPL) ===')
try:
    us_news = requests.get('http://localhost:8001/api/news/stock/AAPL?market=US&limit=5', headers=headers, timeout=30)
    print(f'Status: {us_news.status_code}')
    data = us_news.json()
    print(f'Total: {data.get("total", 0)}')
    print(f'Source: {data.get("source", "N/A")}')
    if data.get('news'):
        for i, news in enumerate(data['news'][:3]):
            print(f'  {i+1}. {news.get("title", "N/A")[:70]}...')
            print(f'     Source: {news.get("source", "N/A")}')
            print(f'     URL: {news.get("source_url", "N/A")[:50]}...' if news.get("source_url") else '')
    else:
        print('  No news found')
except Exception as e:
    print(f'Error: {e}')

# Test US market news
print('\n=== Testing US Market News ===')
try:
    us_market = requests.get('http://localhost:8001/api/news/market?market=US&limit=5', headers=headers, timeout=30)
    print(f'Status: {us_market.status_code}')
    data = us_market.json()
    print(f'Total: {data.get("total", 0)}')
    if data.get('news'):
        for i, news in enumerate(data['news'][:3]):
            print(f'  {i+1}. {news.get("title", "N/A")[:70]}...')
            print(f'     Source: {news.get("source", "N/A")}')
    else:
        print('  No news found')
except Exception as e:
    print(f'Error: {e}')

# Test TW news (should still work)
print('\n=== Testing TW Market News ===')
try:
    tw_news = requests.get('http://localhost:8001/api/news/market?market=TW&limit=3', headers=headers, timeout=30)
    print(f'Status: {tw_news.status_code}')
    data = tw_news.json()
    print(f'Total: {data.get("total", 0)}')
    if data.get('news'):
        for i, news in enumerate(data['news'][:2]):
            print(f'  {i+1}. {news.get("title", "N/A")[:50]}...')
    else:
        print('  No news found')
except Exception as e:
    print(f'Error: {e}')
