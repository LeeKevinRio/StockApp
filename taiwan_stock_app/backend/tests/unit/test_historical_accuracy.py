"""
_compute_historical_accuracy 單元測試

鎖定 ai router 內 _compute_historical_accuracy 的回傳格式：
- < 3 筆 → None（避免少量樣本誤導）
- >= 3 筆 → dict 含 direction_accuracy_percent / avg_error_percent /
  amplitude_ratio / n_records

iter 6 加入後，在快取的 AI 報告路徑也會帶 historical_accuracy，這個
信任徽章是預測產品化的關鍵 UX 訊號。
"""
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models import PredictionRecord
from app.routers.ai import _compute_historical_accuracy


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _make_record(
    stock_id: str,
    days_ago: int,
    predicted_change: float,
    actual_change: float,
    correct: bool,
    error: float,
):
    """建立一筆已驗證的 PredictionRecord"""
    return PredictionRecord(
        stock_id=stock_id,
        stock_name="Test",
        market_region="TW",
        prediction_date=date.today() - timedelta(days=days_ago + 1),
        target_date=date.today() - timedelta(days=days_ago),
        predicted_direction="UP" if predicted_change >= 0 else "DOWN",
        predicted_change_percent=Decimal(str(predicted_change)),
        predicted_probability=Decimal("0.65"),
        base_close_price=Decimal("100"),
        actual_close_price=Decimal(str(100 + actual_change)),
        actual_change_percent=Decimal(str(actual_change)),
        actual_direction="UP" if actual_change >= 0 else "DOWN",
        direction_correct=correct,
        error_percent=Decimal(str(error)),
    )


def test_returns_none_when_less_than_3_records(db_session):
    """少於 3 筆 → None（避免少量樣本給人誤導性的 100% 準確率）"""
    db_session.add(_make_record("2330", 1, 1.0, 0.5, True, 0.5))
    db_session.add(_make_record("2330", 2, -0.5, -0.3, True, 0.2))
    db_session.commit()

    result = _compute_historical_accuracy(db_session, "2330")
    assert result is None


def test_returns_stats_with_3_or_more_records(db_session):
    """3 筆即可產生統計（與 ai_suggestion_service _get_accuracy_feedback 門檻一致）"""
    db_session.add(_make_record("2330", 1, 1.0, 0.5, True, 0.5))
    db_session.add(_make_record("2330", 2, -0.5, -0.3, True, 0.2))
    db_session.add(_make_record("2330", 3, 2.0, -0.5, False, 2.5))
    db_session.commit()

    result = _compute_historical_accuracy(db_session, "2330")
    assert result is not None
    assert result["n_records"] == 3
    # 2 / 3 ≈ 66.7%
    assert result["direction_accuracy_percent"] == pytest.approx(66.7, abs=0.1)
    # avg of 0.5, 0.2, 2.5 = 1.0666... → 1.07
    assert result["avg_error_percent"] == pytest.approx(1.07, abs=0.05)


def test_filters_by_stock_id(db_session):
    """不同 stock_id 不混淆"""
    db_session.add(_make_record("2330", 1, 1.0, 1.0, True, 0))
    db_session.add(_make_record("2330", 2, 1.0, 1.0, True, 0))
    db_session.add(_make_record("2330", 3, 1.0, 1.0, True, 0))
    db_session.add(_make_record("2454", 1, 1.0, -1.0, False, 2.0))
    db_session.commit()

    result_2330 = _compute_historical_accuracy(db_session, "2330")
    assert result_2330["n_records"] == 3
    assert result_2330["direction_accuracy_percent"] == 100.0

    # 2454 只有 1 筆 → None
    result_2454 = _compute_historical_accuracy(db_session, "2454")
    assert result_2454 is None


def test_skips_records_without_actual_price(db_session):
    """尚未驗證的預測（actual_close_price=None）不計入"""
    # 3 筆已驗證
    db_session.add(_make_record("2330", 1, 1.0, 1.0, True, 0))
    db_session.add(_make_record("2330", 2, 1.0, 1.0, True, 0))
    db_session.add(_make_record("2330", 3, -1.0, -1.0, True, 0))

    # 1 筆未驗證
    pending = PredictionRecord(
        stock_id="2330",
        stock_name="Test",
        market_region="TW",
        prediction_date=date.today(),
        target_date=date.today() + timedelta(days=1),
        predicted_direction="UP",
        predicted_change_percent=Decimal("1.5"),
        predicted_probability=Decimal("0.7"),
        base_close_price=Decimal("100"),
        actual_close_price=None,
    )
    db_session.add(pending)
    db_session.commit()

    result = _compute_historical_accuracy(db_session, "2330")
    assert result["n_records"] == 3
    assert result["direction_accuracy_percent"] == 100.0


def test_amplitude_ratio_reflects_overshoot(db_session):
    """預測幅度 vs 實際幅度比值（過度自信時 > 1）"""
    # 預測 ±2%，實際 ±1% → ratio = 2.0
    db_session.add(_make_record("2330", 1, 2.0, 1.0, True, 1.0))
    db_session.add(_make_record("2330", 2, -2.0, -1.0, True, 1.0))
    db_session.add(_make_record("2330", 3, 2.0, 1.0, True, 1.0))
    db_session.commit()

    result = _compute_historical_accuracy(db_session, "2330")
    assert result["amplitude_ratio"] == pytest.approx(2.0, abs=0.01)
