"""
技術指標計算服務
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class TechnicalIndicators:
    """技術指標計算器"""

    @staticmethod
    def calculate_ma(prices: pd.Series, period: int) -> pd.Series:
        """計算移動平均線 (MA)"""
        return prices.rolling(window=period).mean()

    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """計算指數移動平均線 (EMA)"""
        return prices.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """計算相對強弱指標 (RSI)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_macd(
        prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9
    ) -> Dict[str, pd.Series]:
        """
        計算MACD指標
        Returns:
            {
                'macd': MACD線 (快線 - 慢線),
                'signal': 信號線 (MACD的9日EMA),
                'histogram': 柱狀圖 (MACD - 信號線)
            }
        """
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd": macd_line,
            "signal": signal_line,
            "histogram": histogram,
        }

    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series, period: int = 20, std_dev: float = 2.0
    ) -> Dict[str, pd.Series]:
        """
        計算布林通道
        Returns:
            {
                'upper': 上軌,
                'middle': 中軌 (MA20),
                'lower': 下軌
            }
        """
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return {"upper": upper, "middle": middle, "lower": lower}

    @staticmethod
    def calculate_kd(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 9
    ) -> Dict[str, pd.Series]:
        """
        計算KD指標 (隨機指標)
        Returns:
            {
                'k': K值,
                'd': D值
            }
        """
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()

        rsv = 100 * (close - lowest_low) / (highest_high - lowest_low)
        k = rsv.ewm(alpha=1 / 3, adjust=False).mean()
        d = k.ewm(alpha=1 / 3, adjust=False).mean()

        return {"k": k, "d": d}

    @staticmethod
    def calculate_williams_r(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """
        計算威廉指標 (%R)
        值介於 -100 到 0 之間
        -20 以上為超買，-80 以下為超賣
        """
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()

        williams_r = -100 * (highest_high - close) / (highest_high - lowest_low)
        return williams_r

    @staticmethod
    def calculate_obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """
        計算能量潮指標 (OBV)
        根據價格變動累加/減少成交量
        """
        obv = pd.Series(index=close.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]

        for i in range(1, len(close)):
            if close.iloc[i] > close.iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i - 1]

        return obv

    @staticmethod
    def calculate_atr(
        high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14
    ) -> pd.Series:
        """
        計算平均真實波幅 (ATR)
        用於衡量市場波動性
        """
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())

        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()

        return atr

    @staticmethod
    def calculate_all_indicators(df: pd.DataFrame) -> Dict:
        """
        計算所有技術指標

        Args:
            df: 包含 'open', 'high', 'low', 'close', 'volume' 欄位的 DataFrame

        Returns:
            包含所有指標的字典
        """
        if len(df) < 30:
            return {}

        result = {}

        try:
            # 移動平均線
            result["ma5"] = TechnicalIndicators.calculate_ma(df["close"], 5)
            result["ma10"] = TechnicalIndicators.calculate_ma(df["close"], 10)
            result["ma20"] = TechnicalIndicators.calculate_ma(df["close"], 20)
            result["ma60"] = TechnicalIndicators.calculate_ma(df["close"], 60)

            # RSI
            result["rsi"] = TechnicalIndicators.calculate_rsi(df["close"], 14)

            # MACD
            macd_data = TechnicalIndicators.calculate_macd(df["close"])
            result["macd"] = macd_data["macd"]
            result["macd_signal"] = macd_data["signal"]
            result["macd_histogram"] = macd_data["histogram"]

            # 布林通道
            bb_data = TechnicalIndicators.calculate_bollinger_bands(df["close"])
            result["bb_upper"] = bb_data["upper"]
            result["bb_middle"] = bb_data["middle"]
            result["bb_lower"] = bb_data["lower"]

            # KD指標
            kd_data = TechnicalIndicators.calculate_kd(
                df["high"], df["low"], df["close"]
            )
            result["k"] = kd_data["k"]
            result["d"] = kd_data["d"]

            # 威廉指標
            result["williams_r"] = TechnicalIndicators.calculate_williams_r(
                df["high"], df["low"], df["close"]
            )

            # OBV
            result["obv"] = TechnicalIndicators.calculate_obv(
                df["close"], df["volume"]
            )

            # ATR
            result["atr"] = TechnicalIndicators.calculate_atr(
                df["high"], df["low"], df["close"]
            )

        except Exception as e:
            logger.error(f"計算技術指標時發生錯誤: {e}")
            return {}

        return result

    @staticmethod
    def get_latest_indicators(df: pd.DataFrame) -> Dict:
        """
        獲取最新的技術指標值（用於AI分析）

        Returns:
            包含最新指標值的字典
        """
        indicators = TechnicalIndicators.calculate_all_indicators(df)

        if not indicators:
            return {}

        latest = {}
        for key, series in indicators.items():
            if isinstance(series, pd.Series) and len(series) > 0:
                # 獲取最後一個非 NaN 值
                last_valid = series.dropna().iloc[-1] if len(series.dropna()) > 0 else None
                if last_valid is not None:
                    latest[key] = float(last_valid)

        return latest
