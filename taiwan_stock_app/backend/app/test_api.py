"""
測試 API 的腳本
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_register_and_login():
    """註冊測試用戶並登入"""
    # 註冊
    register_data = {
        "email": "test@example.com",
        "password": "test123456",
        "display_name": "測試用戶"
    }

    try:
        response = requests.post(f"{BASE_URL}/api/auth/register", json=register_data)
        print(f"註冊回應: {response.status_code}")
        if response.status_code == 200:
            print(f"註冊成功: {response.json()}")
    except Exception as e:
        print(f"註冊失敗或用戶已存在: {e}")

    # 登入
    login_data = {
        "email": "test@example.com",
        "password": "test123456"
    }

    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print(f"\n登入回應: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(f"登入成功!")
        return result.get("access_token")
    else:
        print(f"登入失敗: {response.text}")
        return None

def test_stock_history(token):
    """測試股票歷史K線數據"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "="*60)
    print("測試 K線數據 API (2330 台積電)")
    print("="*60)

    response = requests.get(
        f"{BASE_URL}/api/stocks/2330/history?days=60",
        headers=headers
    )

    print(f"狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ K線數據載入成功!")
        print(f"   獲取 {len(data)} 筆歷史數據")

        if len(data) > 0:
            latest = data[-1]
            print(f"\n   最新數據:")
            print(f"   日期: {latest['date']}")
            print(f"   開盤: {latest['open']}")
            print(f"   最高: {latest['high']}")
            print(f"   最低: {latest['low']}")
            print(f"   收盤: {latest['close']}")
            print(f"   成交量: {latest['volume']}")

            # 檢查欄位是否正確
            required_fields = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_fields = [f for f in required_fields if f not in latest]
            if missing_fields:
                print(f"\n   ⚠️ 缺少欄位: {missing_fields}")
            else:
                print(f"\n   ✅ 所有必要欄位都存在!")
    else:
        print(f"❌ K線數據載入失敗: {response.text}")

def test_realtime_price(token):
    """測試即時報價"""
    headers = {"Authorization": f"Bearer {token}"}

    print("\n" + "="*60)
    print("測試即時報價 API (2330 台積電)")
    print("="*60)

    response = requests.get(
        f"{BASE_URL}/api/stocks/2330/price",
        headers=headers
    )

    print(f"狀態碼: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 即時報價載入成功!")
        print(f"\n   股票代碼: {data.get('stock_id')}")
        print(f"   股票名稱: {data.get('name')}")
        print(f"   當前價格: {data.get('current_price')}")
        print(f"   漲跌: {data.get('change')}")
        print(f"   漲跌幅: {data.get('change_percent')}%")
        print(f"   開盤: {data.get('open')}")
        print(f"   最高: {data.get('high')}")
        print(f"   最低: {data.get('low')}")
        print(f"   成交量: {data.get('volume')}")
        print(f"   更新時間: {data.get('updated_at')}")
    else:
        print(f"❌ 即時報價載入失敗: {response.text}")

if __name__ == "__main__":
    print("="*60)
    print("台股 AI 投資建議 APP - API 測試")
    print("="*60)

    # 登入獲取 token
    token = test_register_and_login()

    if token:
        # 測試K線數據
        test_stock_history(token)

        # 測試即時報價
        test_realtime_price(token)

        print("\n" + "="*60)
        print("測試完成!")
        print("="*60)
    else:
        print("\n❌ 無法獲取認證 token，測試中止")
