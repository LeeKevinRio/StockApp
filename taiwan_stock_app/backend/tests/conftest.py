"""
Shared test fixtures and configuration
"""
import pytest
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.main import app
from app.database import Base, get_db
from app.models import User, Stock
from app.services import get_password_hash

# Use SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database override"""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user"""
    user = User(
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(client: TestClient, test_user: User) -> dict:
    """Get authentication headers for test user"""
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "testpassword123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_stocks(db: Session) -> list[Stock]:
    """Create sample stocks for testing"""
    stocks = [
        Stock(
            stock_id="2330",
            name="台積電",
            market="TSE",
            industry="半導體業",
        ),
        Stock(
            stock_id="2317",
            name="鴻海",
            market="TSE",
            industry="其他電子業",
        ),
        Stock(
            stock_id="2454",
            name="聯發科",
            market="TSE",
            industry="半導體業",
        ),
    ]
    for stock in stocks:
        db.add(stock)
    db.commit()
    for stock in stocks:
        db.refresh(stock)
    return stocks


@pytest.fixture
def sample_price_data() -> list[dict]:
    """Sample price data for testing"""
    return [
        {"date": "2024-01-01", "open": 100.0, "high": 105.0, "low": 98.0, "close": 103.0, "volume": 10000},
        {"date": "2024-01-02", "open": 103.0, "high": 108.0, "low": 102.0, "close": 107.0, "volume": 12000},
        {"date": "2024-01-03", "open": 107.0, "high": 110.0, "low": 105.0, "close": 106.0, "volume": 11000},
        {"date": "2024-01-04", "open": 106.0, "high": 109.0, "low": 104.0, "close": 108.0, "volume": 13000},
        {"date": "2024-01-05", "open": 108.0, "high": 112.0, "low": 107.0, "close": 111.0, "volume": 15000},
        {"date": "2024-01-08", "open": 111.0, "high": 115.0, "low": 110.0, "close": 114.0, "volume": 18000},
        {"date": "2024-01-09", "open": 114.0, "high": 116.0, "low": 112.0, "close": 113.0, "volume": 14000},
        {"date": "2024-01-10", "open": 113.0, "high": 117.0, "low": 111.0, "close": 116.0, "volume": 16000},
        {"date": "2024-01-11", "open": 116.0, "high": 118.0, "low": 114.0, "close": 115.0, "volume": 12000},
        {"date": "2024-01-12", "open": 115.0, "high": 119.0, "low": 113.0, "close": 118.0, "volume": 17000},
        {"date": "2024-01-15", "open": 118.0, "high": 120.0, "low": 116.0, "close": 117.0, "volume": 14000},
        {"date": "2024-01-16", "open": 117.0, "high": 121.0, "low": 115.0, "close": 120.0, "volume": 19000},
        {"date": "2024-01-17", "open": 120.0, "high": 122.0, "low": 118.0, "close": 119.0, "volume": 15000},
        {"date": "2024-01-18", "open": 119.0, "high": 123.0, "low": 117.0, "close": 122.0, "volume": 20000},
        {"date": "2024-01-19", "open": 122.0, "high": 125.0, "low": 120.0, "close": 124.0, "volume": 22000},
    ]
