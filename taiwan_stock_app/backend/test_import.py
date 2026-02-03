#!/usr/bin/env python
import sys
print("Python:", sys.executable)
print("Testing imports...")

try:
    print("1. Testing database...")
    from app.database import Base, engine
    print("   OK")
except Exception as e:
    print(f"   ERROR: {e}")

try:
    print("2. Testing models...")
    from app.models import User, Stock, Watchlist
    print("   OK")
except Exception as e:
    print(f"   ERROR: {e}")

try:
    print("3. Testing trading model...")
    from app.models.trading import VirtualAccount, VirtualPosition, VirtualOrder
    print("   OK")
except Exception as e:
    print(f"   ERROR: {e}")

try:
    print("4. Testing portfolio model...")
    from app.models.portfolio import Portfolio, PortfolioHolding, PortfolioSnapshot
    print("   OK")
except Exception as e:
    print(f"   ERROR: {e}")

try:
    print("5. Testing routers...")
    from app.routers import auth_router, stocks_router, trading_router, portfolio_router
    print("   OK")
except Exception as e:
    print(f"   ERROR: {e}")

try:
    print("6. Testing main app...")
    from app.main import app
    print("   OK")
except Exception as e:
    print(f"   ERROR: {e}")

print("\nAll imports tested!")
