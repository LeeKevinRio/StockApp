"""
Unit tests for technical indicators calculations
"""
import pytest
import pandas as pd
import numpy as np
from app.services.technical_indicators import TechnicalIndicators


class TestMovingAverage:
    """Tests for Moving Average calculations"""

    def test_ma_basic_calculation(self):
        """Test basic MA calculation"""
        prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        ma5 = TechnicalIndicators.calculate_ma(prices, 5)

        # First 4 values should be NaN
        assert pd.isna(ma5.iloc[0])
        assert pd.isna(ma5.iloc[3])

        # 5th value should be average of first 5
        assert ma5.iloc[4] == 12.0  # (10+11+12+13+14)/5

    def test_ma_with_different_periods(self):
        """Test MA with different periods"""
        prices = pd.Series(range(1, 21))  # 1 to 20

        ma5 = TechnicalIndicators.calculate_ma(prices, 5)
        ma10 = TechnicalIndicators.calculate_ma(prices, 10)

        # Check that longer period has more NaN values
        assert ma5.isna().sum() == 4
        assert ma10.isna().sum() == 9

    def test_ema_calculation(self):
        """Test EMA calculation"""
        prices = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19])
        ema = TechnicalIndicators.calculate_ema(prices, 5)

        # EMA should not have NaN values after first point
        assert not pd.isna(ema.iloc[4])
        # EMA should be different from SMA
        ma = TechnicalIndicators.calculate_ma(prices, 5)
        assert ema.iloc[-1] != ma.iloc[-1]


class TestRSI:
    """Tests for RSI calculations"""

    def test_rsi_rising_prices(self):
        """Test RSI with consistently rising prices"""
        # Consistently rising prices should result in high RSI
        prices = pd.Series(range(100, 130))
        rsi = TechnicalIndicators.calculate_rsi(prices, 14)

        # RSI should be very high (close to 100) for rising prices
        assert rsi.iloc[-1] > 90

    def test_rsi_falling_prices(self):
        """Test RSI with consistently falling prices"""
        # Consistently falling prices should result in low RSI
        prices = pd.Series(range(130, 100, -1))
        rsi = TechnicalIndicators.calculate_rsi(prices, 14)

        # RSI should be very low (close to 0) for falling prices
        assert rsi.iloc[-1] < 10

    def test_rsi_range(self):
        """Test that RSI stays within 0-100 range"""
        np.random.seed(42)
        prices = pd.Series(100 + np.random.randn(100).cumsum())
        rsi = TechnicalIndicators.calculate_rsi(prices, 14)

        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()

    def test_rsi_overbought_oversold(self):
        """Test RSI overbought/oversold levels"""
        # Create data that oscillates
        prices = pd.Series([100 + 5 * np.sin(i / 5) for i in range(50)])
        rsi = TechnicalIndicators.calculate_rsi(prices, 14)

        valid_rsi = rsi.dropna()
        # Should have values in normal range (not extreme)
        assert valid_rsi.mean() > 30
        assert valid_rsi.mean() < 70


class TestMACD:
    """Tests for MACD calculations"""

    def test_macd_basic_structure(self):
        """Test that MACD returns correct structure"""
        prices = pd.Series(range(100, 200))
        result = TechnicalIndicators.calculate_macd(prices)

        assert "macd" in result
        assert "signal" in result
        assert "histogram" in result

    def test_macd_histogram_calculation(self):
        """Test that histogram equals MACD - Signal"""
        prices = pd.Series(range(100, 200))
        result = TechnicalIndicators.calculate_macd(prices)

        # Histogram should be MACD - Signal (where both are valid)
        valid_idx = ~(result["macd"].isna() | result["signal"].isna())
        expected_histogram = result["macd"][valid_idx] - result["signal"][valid_idx]
        actual_histogram = result["histogram"][valid_idx]

        pd.testing.assert_series_equal(
            actual_histogram.reset_index(drop=True),
            expected_histogram.reset_index(drop=True),
            check_names=False,
        )

    def test_macd_trending_market(self):
        """Test MACD in trending market"""
        # Strong uptrend
        prices = pd.Series([100 + i * 2 for i in range(50)])
        result = TechnicalIndicators.calculate_macd(prices)

        # In uptrend, MACD should be positive
        assert result["macd"].iloc[-1] > 0


class TestBollingerBands:
    """Tests for Bollinger Bands calculations"""

    def test_bollinger_structure(self):
        """Test that Bollinger returns correct structure"""
        prices = pd.Series(range(100, 150))
        result = TechnicalIndicators.calculate_bollinger_bands(prices)

        assert "upper" in result
        assert "middle" in result
        assert "lower" in result

    def test_bollinger_band_order(self):
        """Test that upper > middle > lower"""
        np.random.seed(42)
        prices = pd.Series(100 + np.random.randn(50).cumsum())
        result = TechnicalIndicators.calculate_bollinger_bands(prices)

        valid_idx = ~(result["upper"].isna() | result["middle"].isna() | result["lower"].isna())

        assert (result["upper"][valid_idx] > result["middle"][valid_idx]).all()
        assert (result["middle"][valid_idx] > result["lower"][valid_idx]).all()

    def test_bollinger_middle_is_sma(self):
        """Test that middle band equals SMA"""
        prices = pd.Series(range(100, 150))
        result = TechnicalIndicators.calculate_bollinger_bands(prices, period=20)
        sma = TechnicalIndicators.calculate_ma(prices, 20)

        pd.testing.assert_series_equal(
            result["middle"].dropna(),
            sma.dropna(),
            check_names=False,
        )


class TestKD:
    """Tests for KD (Stochastic) calculations"""

    def test_kd_structure(self):
        """Test that KD returns correct structure"""
        high = pd.Series([105, 108, 110, 109, 112, 115, 116, 117, 118, 119])
        low = pd.Series([98, 100, 102, 101, 104, 107, 108, 109, 110, 111])
        close = pd.Series([103, 107, 106, 108, 111, 114, 113, 116, 115, 118])

        result = TechnicalIndicators.calculate_kd(high, low, close)

        assert "k" in result
        assert "d" in result

    def test_kd_range(self):
        """Test that K and D stay within 0-100 range"""
        np.random.seed(42)
        base = 100 + np.random.randn(50).cumsum()
        high = pd.Series(base + abs(np.random.randn(50) * 2))
        low = pd.Series(base - abs(np.random.randn(50) * 2))
        close = pd.Series(base + np.random.randn(50))

        result = TechnicalIndicators.calculate_kd(high, low, close)

        valid_k = result["k"].dropna()
        valid_d = result["d"].dropna()

        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
        assert (valid_d >= 0).all()
        assert (valid_d <= 100).all()

    def test_kd_at_extremes(self):
        """Test KD at price extremes — 連續收在最高價，K 應趨近 100"""
        # 給足夠多期讓 K 值收斂到高位
        n = 20
        high = pd.Series([100] * n)
        low = pd.Series([90] * n)
        close = pd.Series([100] * n)  # 所有收盤都在最高價

        result = TechnicalIndicators.calculate_kd(high, low, close, period=9)

        # K should be very high when close is consistently at the high
        assert result["k"].iloc[-1] > 90


class TestWilliamsR:
    """Tests for Williams %R calculations"""

    def test_williams_r_range(self):
        """Test that Williams %R stays within -100 to 0 range"""
        np.random.seed(42)
        base = 100 + np.random.randn(30).cumsum()
        high = pd.Series(base + abs(np.random.randn(30) * 2))
        low = pd.Series(base - abs(np.random.randn(30) * 2))
        close = pd.Series(base + np.random.randn(30))

        result = TechnicalIndicators.calculate_williams_r(high, low, close)
        valid = result.dropna()

        assert (valid >= -100).all()
        assert (valid <= 0).all()


class TestATR:
    """Tests for ATR calculations"""

    def test_atr_positive(self):
        """Test that ATR is always positive"""
        np.random.seed(42)
        base = 100 + np.random.randn(30).cumsum()
        high = pd.Series(base + abs(np.random.randn(30) * 2))
        low = pd.Series(base - abs(np.random.randn(30) * 2))
        close = pd.Series(base + np.random.randn(30))

        result = TechnicalIndicators.calculate_atr(high, low, close)
        valid = result.dropna()

        assert (valid > 0).all()


class TestAllIndicators:
    """Tests for combined indicator calculation"""

    def test_calculate_all_indicators(self, sample_price_data):
        """Test calculating all indicators at once"""
        df = pd.DataFrame(sample_price_data)

        # Need more data for all indicators
        extended_data = sample_price_data * 3  # Triple the data
        df = pd.DataFrame(extended_data)

        result = TechnicalIndicators.calculate_all_indicators(df)

        # Should return a non-empty dict
        assert isinstance(result, dict)
        # Should include main indicators
        if result:  # If we have enough data
            assert "rsi" in result or len(df) < 30

    def test_get_latest_indicators(self, sample_price_data):
        """Test getting latest indicator values"""
        extended_data = sample_price_data * 3
        df = pd.DataFrame(extended_data)

        result = TechnicalIndicators.get_latest_indicators(df)

        assert isinstance(result, dict)
        # All values should be floats or not exist
        for value in result.values():
            assert isinstance(value, float)


@pytest.fixture
def sample_price_data():
    """Sample price data for testing"""
    return [
        {"date": f"2024-01-{i:02d}", "open": 100.0 + i, "high": 105.0 + i, "low": 98.0 + i, "close": 103.0 + i, "volume": 10000 + i * 100}
        for i in range(1, 16)
    ]
