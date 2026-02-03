"""
Pattern Recognition Service
專業級高風險交易分析平台 - 形態識別服務

識別常見的技術分析形態：
- 頭肩頂/頭肩底 (Head and Shoulders)
- 雙頂/雙底 (Double Top/Bottom)
- 三角形整理 (Triangle Patterns)
- 楔形 (Wedge Patterns)
- 旗形和矩形 (Flag and Rectangle)
- 突破確認信號
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd


def argrelextrema(data: np.ndarray, comparator, order: int = 1):
    """
    找出局部極值的索引
    替代 scipy.signal.argrelextrema
    """
    result = []
    for i in range(order, len(data) - order):
        is_extrema = True
        for j in range(1, order + 1):
            if not comparator(data[i], data[i - j]) or not comparator(data[i], data[i + j]):
                is_extrema = False
                break
        if is_extrema:
            result.append(i)
    return (np.array(result),)


class PatternType(str, Enum):
    """形態類型"""
    HEAD_SHOULDERS_TOP = "head_shoulders_top"  # 頭肩頂
    HEAD_SHOULDERS_BOTTOM = "head_shoulders_bottom"  # 頭肩底
    DOUBLE_TOP = "double_top"  # 雙頂
    DOUBLE_BOTTOM = "double_bottom"  # 雙底
    TRIPLE_TOP = "triple_top"  # 三重頂
    TRIPLE_BOTTOM = "triple_bottom"  # 三重底
    ASCENDING_TRIANGLE = "ascending_triangle"  # 上升三角形
    DESCENDING_TRIANGLE = "descending_triangle"  # 下降三角形
    SYMMETRIC_TRIANGLE = "symmetric_triangle"  # 對稱三角形
    RISING_WEDGE = "rising_wedge"  # 上升楔形
    FALLING_WEDGE = "falling_wedge"  # 下降楔形
    BULL_FLAG = "bull_flag"  # 多頭旗形
    BEAR_FLAG = "bear_flag"  # 空頭旗形
    RECTANGLE = "rectangle"  # 矩形整理
    BREAKOUT_UP = "breakout_up"  # 向上突破
    BREAKOUT_DOWN = "breakout_down"  # 向下突破


class PatternSignal(str, Enum):
    """形態信號方向"""
    BULLISH = "bullish"  # 看多
    BEARISH = "bearish"  # 看空
    NEUTRAL = "neutral"  # 中性


@dataclass
class DetectedPattern:
    """檢測到的形態"""
    pattern_type: PatternType
    signal: PatternSignal
    confidence: float  # 信心度 0-100
    start_index: int
    end_index: int
    key_prices: Dict[str, float]  # 關鍵價位
    target_price: Optional[float]  # 目標價
    stop_loss: Optional[float]  # 建議停損
    description: str  # 形態描述
    is_confirmed: bool  # 是否已確認突破


class PatternRecognitionService:
    """形態識別服務"""

    def __init__(self):
        self.min_pattern_length = 10  # 最小形態長度
        self.max_pattern_length = 60  # 最大形態長度

    def find_local_extrema(
        self,
        prices: np.ndarray,
        order: int = 5
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        尋找局部極值點

        Args:
            prices: 價格序列
            order: 比較鄰近點的數量

        Returns:
            (局部最大值索引, 局部最小值索引)
        """
        local_max_idx = argrelextrema(prices, np.greater, order=order)[0]
        local_min_idx = argrelextrema(prices, np.less, order=order)[0]
        return local_max_idx, local_min_idx

    def detect_all_patterns(
        self,
        df: pd.DataFrame,
        lookback: int = 60
    ) -> List[DetectedPattern]:
        """
        檢測所有形態

        Args:
            df: 包含 OHLCV 數據的 DataFrame
            lookback: 回顧期間

        Returns:
            檢測到的形態列表
        """
        if len(df) < self.min_pattern_length:
            return []

        # 使用最近 lookback 天的數據
        df_subset = df.tail(lookback).copy()
        df_subset = df_subset.reset_index(drop=True)

        high = df_subset['high'].values
        low = df_subset['low'].values
        close = df_subset['close'].values

        patterns = []

        # 檢測各種形態
        patterns.extend(self._detect_head_shoulders(high, low, close))
        patterns.extend(self._detect_double_patterns(high, low, close))
        patterns.extend(self._detect_triangles(high, low, close))
        patterns.extend(self._detect_wedges(high, low, close))
        patterns.extend(self._detect_flags(high, low, close))
        patterns.extend(self._detect_breakouts(high, low, close))

        # 按信心度排序
        patterns.sort(key=lambda x: x.confidence, reverse=True)

        return patterns

    def _detect_head_shoulders(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測頭肩形態"""
        patterns = []

        # 尋找極值點
        max_idx, min_idx = self.find_local_extrema(high, order=3)

        if len(max_idx) < 3:
            return patterns

        # 檢測頭肩頂
        for i in range(len(max_idx) - 2):
            left_shoulder_idx = max_idx[i]
            head_idx = max_idx[i + 1]
            right_shoulder_idx = max_idx[i + 2]

            left_shoulder = high[left_shoulder_idx]
            head = high[head_idx]
            right_shoulder = high[right_shoulder_idx]

            # 頭部必須高於兩肩
            if head > left_shoulder and head > right_shoulder:
                # 兩肩高度應該接近 (差距不超過 5%)
                shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
                if shoulder_diff < 0.05:
                    # 找頸線（兩肩之間的最低點）
                    neckline_region = low[left_shoulder_idx:right_shoulder_idx+1]
                    neckline = np.min(neckline_region)

                    # 計算目標價（頭部到頸線的距離向下延伸）
                    pattern_height = head - neckline
                    target = neckline - pattern_height

                    # 檢查是否突破頸線
                    current_price = close[-1]
                    is_confirmed = current_price < neckline

                    confidence = self._calculate_pattern_confidence(
                        shoulder_diff,
                        pattern_height / head,
                        is_confirmed
                    )

                    if confidence > 50:
                        patterns.append(DetectedPattern(
                            pattern_type=PatternType.HEAD_SHOULDERS_TOP,
                            signal=PatternSignal.BEARISH,
                            confidence=confidence,
                            start_index=left_shoulder_idx,
                            end_index=right_shoulder_idx,
                            key_prices={
                                "left_shoulder": float(left_shoulder),
                                "head": float(head),
                                "right_shoulder": float(right_shoulder),
                                "neckline": float(neckline),
                            },
                            target_price=float(target),
                            stop_loss=float(head * 1.02),  # 頭部上方 2%
                            description=f"頭肩頂形態：頭部 {head:.2f}，頸線 {neckline:.2f}",
                            is_confirmed=is_confirmed,
                        ))

        # 檢測頭肩底（邏輯相反）
        min_idx, _ = self.find_local_extrema(low, order=3)

        if len(min_idx) >= 3:
            for i in range(len(min_idx) - 2):
                left_shoulder_idx = min_idx[i]
                head_idx = min_idx[i + 1]
                right_shoulder_idx = min_idx[i + 2]

                left_shoulder = low[left_shoulder_idx]
                head = low[head_idx]
                right_shoulder = low[right_shoulder_idx]

                if head < left_shoulder and head < right_shoulder:
                    shoulder_diff = abs(left_shoulder - right_shoulder) / left_shoulder
                    if shoulder_diff < 0.05:
                        neckline_region = high[left_shoulder_idx:right_shoulder_idx+1]
                        neckline = np.max(neckline_region)

                        pattern_height = neckline - head
                        target = neckline + pattern_height

                        current_price = close[-1]
                        is_confirmed = current_price > neckline

                        confidence = self._calculate_pattern_confidence(
                            shoulder_diff,
                            pattern_height / head,
                            is_confirmed
                        )

                        if confidence > 50:
                            patterns.append(DetectedPattern(
                                pattern_type=PatternType.HEAD_SHOULDERS_BOTTOM,
                                signal=PatternSignal.BULLISH,
                                confidence=confidence,
                                start_index=left_shoulder_idx,
                                end_index=right_shoulder_idx,
                                key_prices={
                                    "left_shoulder": float(left_shoulder),
                                    "head": float(head),
                                    "right_shoulder": float(right_shoulder),
                                    "neckline": float(neckline),
                                },
                                target_price=float(target),
                                stop_loss=float(head * 0.98),
                                description=f"頭肩底形態：頭部 {head:.2f}，頸線 {neckline:.2f}",
                                is_confirmed=is_confirmed,
                            ))

        return patterns

    def _detect_double_patterns(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測雙頂/雙底形態"""
        patterns = []

        # 檢測雙頂
        max_idx, _ = self.find_local_extrema(high, order=5)

        if len(max_idx) >= 2:
            for i in range(len(max_idx) - 1):
                first_top_idx = max_idx[i]
                second_top_idx = max_idx[i + 1]

                first_top = high[first_top_idx]
                second_top = high[second_top_idx]

                # 兩個頂部高度應該接近 (差距不超過 3%)
                top_diff = abs(first_top - second_top) / first_top
                if top_diff < 0.03:
                    # 找中間的低點作為頸線
                    valley_region = low[first_top_idx:second_top_idx+1]
                    neckline = np.min(valley_region)

                    pattern_height = max(first_top, second_top) - neckline
                    target = neckline - pattern_height

                    current_price = close[-1]
                    is_confirmed = current_price < neckline

                    confidence = self._calculate_pattern_confidence(
                        top_diff,
                        pattern_height / first_top,
                        is_confirmed
                    )

                    if confidence > 50:
                        patterns.append(DetectedPattern(
                            pattern_type=PatternType.DOUBLE_TOP,
                            signal=PatternSignal.BEARISH,
                            confidence=confidence,
                            start_index=first_top_idx,
                            end_index=second_top_idx,
                            key_prices={
                                "first_top": float(first_top),
                                "second_top": float(second_top),
                                "neckline": float(neckline),
                            },
                            target_price=float(target),
                            stop_loss=float(max(first_top, second_top) * 1.02),
                            description=f"雙頂形態：頂部 {first_top:.2f}/{second_top:.2f}，頸線 {neckline:.2f}",
                            is_confirmed=is_confirmed,
                        ))

        # 檢測雙底
        _, min_idx = self.find_local_extrema(low, order=5)

        if len(min_idx) >= 2:
            for i in range(len(min_idx) - 1):
                first_bottom_idx = min_idx[i]
                second_bottom_idx = min_idx[i + 1]

                first_bottom = low[first_bottom_idx]
                second_bottom = low[second_bottom_idx]

                bottom_diff = abs(first_bottom - second_bottom) / first_bottom
                if bottom_diff < 0.03:
                    peak_region = high[first_bottom_idx:second_bottom_idx+1]
                    neckline = np.max(peak_region)

                    pattern_height = neckline - min(first_bottom, second_bottom)
                    target = neckline + pattern_height

                    current_price = close[-1]
                    is_confirmed = current_price > neckline

                    confidence = self._calculate_pattern_confidence(
                        bottom_diff,
                        pattern_height / first_bottom,
                        is_confirmed
                    )

                    if confidence > 50:
                        patterns.append(DetectedPattern(
                            pattern_type=PatternType.DOUBLE_BOTTOM,
                            signal=PatternSignal.BULLISH,
                            confidence=confidence,
                            start_index=first_bottom_idx,
                            end_index=second_bottom_idx,
                            key_prices={
                                "first_bottom": float(first_bottom),
                                "second_bottom": float(second_bottom),
                                "neckline": float(neckline),
                            },
                            target_price=float(target),
                            stop_loss=float(min(first_bottom, second_bottom) * 0.98),
                            description=f"雙底形態：底部 {first_bottom:.2f}/{second_bottom:.2f}，頸線 {neckline:.2f}",
                            is_confirmed=is_confirmed,
                        ))

        return patterns

    def _detect_triangles(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測三角形形態"""
        patterns = []

        if len(high) < 20:
            return patterns

        # 使用最近的數據
        recent_high = high[-30:]
        recent_low = low[-30:]
        recent_close = close[-30:]

        # 計算高點和低點的趨勢線
        x = np.arange(len(recent_high))

        # 找局部極值
        max_idx, min_idx = self.find_local_extrema(recent_high, order=3)
        _, low_min_idx = self.find_local_extrema(recent_low, order=3)

        if len(max_idx) < 2 or len(low_min_idx) < 2:
            return patterns

        # 計算高點趨勢（阻力線斜率）
        high_points = recent_high[max_idx]
        high_slope = np.polyfit(max_idx, high_points, 1)[0] if len(max_idx) >= 2 else 0

        # 計算低點趨勢（支撐線斜率）
        low_points = recent_low[low_min_idx]
        low_slope = np.polyfit(low_min_idx, low_points, 1)[0] if len(low_min_idx) >= 2 else 0

        # 判斷三角形類型
        current_price = recent_close[-1]
        avg_price = np.mean(recent_close)
        pattern_range = np.max(recent_high) - np.min(recent_low)

        # 上升三角形：阻力線水平，支撐線上升
        if abs(high_slope) < 0.1 and low_slope > 0.1:
            resistance = np.mean(high_points[-2:])
            is_confirmed = current_price > resistance

            target = resistance + pattern_range * 0.8
            stop_loss = np.min(recent_low[-5:]) * 0.98

            confidence = 65 + (10 if is_confirmed else 0)

            patterns.append(DetectedPattern(
                pattern_type=PatternType.ASCENDING_TRIANGLE,
                signal=PatternSignal.BULLISH,
                confidence=confidence,
                start_index=len(close) - 30,
                end_index=len(close) - 1,
                key_prices={
                    "resistance": float(resistance),
                    "support_slope": float(low_slope),
                },
                target_price=float(target),
                stop_loss=float(stop_loss),
                description=f"上升三角形：阻力線 {resistance:.2f}，等待突破",
                is_confirmed=is_confirmed,
            ))

        # 下降三角形：支撐線水平，阻力線下降
        elif abs(low_slope) < 0.1 and high_slope < -0.1:
            support = np.mean(low_points[-2:])
            is_confirmed = current_price < support

            target = support - pattern_range * 0.8
            stop_loss = np.max(recent_high[-5:]) * 1.02

            confidence = 65 + (10 if is_confirmed else 0)

            patterns.append(DetectedPattern(
                pattern_type=PatternType.DESCENDING_TRIANGLE,
                signal=PatternSignal.BEARISH,
                confidence=confidence,
                start_index=len(close) - 30,
                end_index=len(close) - 1,
                key_prices={
                    "support": float(support),
                    "resistance_slope": float(high_slope),
                },
                target_price=float(target),
                stop_loss=float(stop_loss),
                description=f"下降三角形：支撐線 {support:.2f}，注意跌破",
                is_confirmed=is_confirmed,
            ))

        # 對稱三角形：兩條線收斂
        elif high_slope < -0.05 and low_slope > 0.05:
            # 計算收斂點
            apex_x = (low_points[0] - high_points[0]) / (high_slope - low_slope) if (high_slope - low_slope) != 0 else 0

            # 判斷突破方向
            mid_price = (np.mean(high_points) + np.mean(low_points)) / 2
            breakout_up = current_price > mid_price

            target = current_price + pattern_range * 0.5 * (1 if breakout_up else -1)
            stop_loss = mid_price * (0.98 if breakout_up else 1.02)

            confidence = 60

            patterns.append(DetectedPattern(
                pattern_type=PatternType.SYMMETRIC_TRIANGLE,
                signal=PatternSignal.BULLISH if breakout_up else PatternSignal.BEARISH,
                confidence=confidence,
                start_index=len(close) - 30,
                end_index=len(close) - 1,
                key_prices={
                    "high_slope": float(high_slope),
                    "low_slope": float(low_slope),
                    "mid_price": float(mid_price),
                },
                target_price=float(target),
                stop_loss=float(stop_loss),
                description=f"對稱三角形：等待方向選擇",
                is_confirmed=False,
            ))

        return patterns

    def _detect_wedges(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測楔形形態"""
        patterns = []

        if len(high) < 20:
            return patterns

        recent_high = high[-25:]
        recent_low = low[-25:]
        recent_close = close[-25:]

        # 計算趨勢
        x = np.arange(len(recent_high))
        high_slope, high_intercept = np.polyfit(x, recent_high, 1)
        low_slope, low_intercept = np.polyfit(x, recent_low, 1)

        current_price = recent_close[-1]

        # 上升楔形：兩條線都向上但收斂（看空）
        if high_slope > 0.05 and low_slope > 0.05 and high_slope < low_slope:
            target = np.min(recent_low)
            stop_loss = np.max(recent_high) * 1.02

            patterns.append(DetectedPattern(
                pattern_type=PatternType.RISING_WEDGE,
                signal=PatternSignal.BEARISH,
                confidence=65,
                start_index=len(close) - 25,
                end_index=len(close) - 1,
                key_prices={
                    "high_slope": float(high_slope),
                    "low_slope": float(low_slope),
                },
                target_price=float(target),
                stop_loss=float(stop_loss),
                description="上升楔形：看空反轉形態",
                is_confirmed=False,
            ))

        # 下降楔形：兩條線都向下但收斂（看多）
        elif high_slope < -0.05 and low_slope < -0.05 and high_slope > low_slope:
            target = np.max(recent_high)
            stop_loss = np.min(recent_low) * 0.98

            patterns.append(DetectedPattern(
                pattern_type=PatternType.FALLING_WEDGE,
                signal=PatternSignal.BULLISH,
                confidence=65,
                start_index=len(close) - 25,
                end_index=len(close) - 1,
                key_prices={
                    "high_slope": float(high_slope),
                    "low_slope": float(low_slope),
                },
                target_price=float(target),
                stop_loss=float(stop_loss),
                description="下降楔形：看多反轉形態",
                is_confirmed=False,
            ))

        return patterns

    def _detect_flags(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測旗形和矩形形態"""
        patterns = []

        if len(high) < 15:
            return patterns

        # 尋找前期趨勢（旗桿）
        pole_period = 10
        flag_period = 5

        if len(close) < pole_period + flag_period:
            return patterns

        pole_close = close[-(pole_period + flag_period):-flag_period]
        flag_close = close[-flag_period:]
        flag_high = high[-flag_period:]
        flag_low = low[-flag_period:]

        # 計算旗桿漲跌幅
        pole_change = (pole_close[-1] - pole_close[0]) / pole_close[0]

        # 計算旗形區間的波動
        flag_range = (np.max(flag_high) - np.min(flag_low)) / np.mean(flag_close)

        # 旗桿必須有明顯漲跌（>5%），旗形區間要小（<3%）
        if abs(pole_change) > 0.05 and flag_range < 0.03:
            current_price = close[-1]

            if pole_change > 0:  # 多頭旗形
                target = current_price + abs(pole_close[-1] - pole_close[0])
                stop_loss = np.min(flag_low) * 0.98

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.BULL_FLAG,
                    signal=PatternSignal.BULLISH,
                    confidence=70,
                    start_index=len(close) - pole_period - flag_period,
                    end_index=len(close) - 1,
                    key_prices={
                        "pole_start": float(pole_close[0]),
                        "pole_end": float(pole_close[-1]),
                        "flag_high": float(np.max(flag_high)),
                        "flag_low": float(np.min(flag_low)),
                    },
                    target_price=float(target),
                    stop_loss=float(stop_loss),
                    description="多頭旗形：延續上漲趨勢",
                    is_confirmed=False,
                ))
            else:  # 空頭旗形
                target = current_price - abs(pole_close[-1] - pole_close[0])
                stop_loss = np.max(flag_high) * 1.02

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.BEAR_FLAG,
                    signal=PatternSignal.BEARISH,
                    confidence=70,
                    start_index=len(close) - pole_period - flag_period,
                    end_index=len(close) - 1,
                    key_prices={
                        "pole_start": float(pole_close[0]),
                        "pole_end": float(pole_close[-1]),
                        "flag_high": float(np.max(flag_high)),
                        "flag_low": float(np.min(flag_low)),
                    },
                    target_price=float(target),
                    stop_loss=float(stop_loss),
                    description="空頭旗形：延續下跌趨勢",
                    is_confirmed=False,
                ))

        # 矩形整理
        recent_high = high[-20:]
        recent_low = low[-20:]

        resistance = np.percentile(recent_high, 90)
        support = np.percentile(recent_low, 10)
        range_pct = (resistance - support) / np.mean(close[-20:])

        # 矩形區間在 2%-8% 之間
        if 0.02 < range_pct < 0.08:
            current_price = close[-1]

            # 判斷突破方向
            if current_price > resistance * 0.995:
                signal = PatternSignal.BULLISH
                target = resistance + (resistance - support)
                stop_loss = support * 0.98
                description = f"矩形整理向上突破：阻力 {resistance:.2f}"
            elif current_price < support * 1.005:
                signal = PatternSignal.BEARISH
                target = support - (resistance - support)
                stop_loss = resistance * 1.02
                description = f"矩形整理向下突破：支撐 {support:.2f}"
            else:
                signal = PatternSignal.NEUTRAL
                target = resistance
                stop_loss = support * 0.98
                description = f"矩形整理中：{support:.2f} - {resistance:.2f}"

            patterns.append(DetectedPattern(
                pattern_type=PatternType.RECTANGLE,
                signal=signal,
                confidence=60,
                start_index=len(close) - 20,
                end_index=len(close) - 1,
                key_prices={
                    "resistance": float(resistance),
                    "support": float(support),
                },
                target_price=float(target),
                stop_loss=float(stop_loss),
                description=description,
                is_confirmed=signal != PatternSignal.NEUTRAL,
            ))

        return patterns

    def _detect_breakouts(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測突破信號"""
        patterns = []

        if len(high) < 20:
            return patterns

        current_price = close[-1]
        prev_close = close[-2] if len(close) > 1 else close[-1]

        # 計算近期高低點
        recent_high = np.max(high[-20:-1])  # 排除今天
        recent_low = np.min(low[-20:-1])

        # 計算 ATR 用於確認突破有效性
        tr = np.maximum(
            high[-20:] - low[-20:],
            np.maximum(
                np.abs(high[-20:] - np.roll(close[-20:], 1)),
                np.abs(low[-20:] - np.roll(close[-20:], 1))
            )
        )
        atr = np.mean(tr[-14:])

        # 向上突破：價格超過近期高點，且漲幅超過 0.5 ATR
        if current_price > recent_high and (current_price - prev_close) > atr * 0.5:
            target = current_price + atr * 2
            stop_loss = recent_high - atr * 0.5

            patterns.append(DetectedPattern(
                pattern_type=PatternType.BREAKOUT_UP,
                signal=PatternSignal.BULLISH,
                confidence=75,
                start_index=len(close) - 1,
                end_index=len(close) - 1,
                key_prices={
                    "breakout_level": float(recent_high),
                    "current_price": float(current_price),
                    "atr": float(atr),
                },
                target_price=float(target),
                stop_loss=float(stop_loss),
                description=f"向上突破 {recent_high:.2f}，成交確認",
                is_confirmed=True,
            ))

        # 向下突破
        if current_price < recent_low and (prev_close - current_price) > atr * 0.5:
            target = current_price - atr * 2
            stop_loss = recent_low + atr * 0.5

            patterns.append(DetectedPattern(
                pattern_type=PatternType.BREAKOUT_DOWN,
                signal=PatternSignal.BEARISH,
                confidence=75,
                start_index=len(close) - 1,
                end_index=len(close) - 1,
                key_prices={
                    "breakout_level": float(recent_low),
                    "current_price": float(current_price),
                    "atr": float(atr),
                },
                target_price=float(target),
                stop_loss=float(stop_loss),
                description=f"向下突破 {recent_low:.2f}，成交確認",
                is_confirmed=True,
            ))

        return patterns

    def _calculate_pattern_confidence(
        self,
        symmetry: float,
        depth: float,
        is_confirmed: bool
    ) -> float:
        """
        計算形態信心度

        Args:
            symmetry: 對稱性（0-1，越小越對稱）
            depth: 深度比例
            is_confirmed: 是否已確認
        """
        base_confidence = 50

        # 對稱性加分（最多 +20）
        symmetry_score = max(0, 20 - symmetry * 400)

        # 深度加分（最多 +15）
        depth_score = min(15, depth * 100)

        # 確認加分（+15）
        confirmation_score = 15 if is_confirmed else 0

        return min(100, base_confidence + symmetry_score + depth_score + confirmation_score)

    def get_pattern_summary(
        self,
        patterns: List[DetectedPattern]
    ) -> Dict:
        """
        生成形態識別摘要

        Args:
            patterns: 檢測到的形態列表

        Returns:
            摘要字典
        """
        if not patterns:
            return {
                "has_patterns": False,
                "dominant_signal": "neutral",
                "patterns_count": 0,
                "summary": "未檢測到明顯形態",
                "top_patterns": [],
            }

        # 統計信號方向
        bullish_count = sum(1 for p in patterns if p.signal == PatternSignal.BULLISH)
        bearish_count = sum(1 for p in patterns if p.signal == PatternSignal.BEARISH)

        # 計算加權信號
        bullish_score = sum(
            p.confidence for p in patterns if p.signal == PatternSignal.BULLISH
        )
        bearish_score = sum(
            p.confidence for p in patterns if p.signal == PatternSignal.BEARISH
        )

        if bullish_score > bearish_score * 1.2:
            dominant_signal = "bullish"
        elif bearish_score > bullish_score * 1.2:
            dominant_signal = "bearish"
        else:
            dominant_signal = "neutral"

        # 取前 3 個最重要的形態
        top_patterns = patterns[:3]

        return {
            "has_patterns": True,
            "dominant_signal": dominant_signal,
            "patterns_count": len(patterns),
            "bullish_count": bullish_count,
            "bearish_count": bearish_count,
            "bullish_score": bullish_score,
            "bearish_score": bearish_score,
            "summary": self._generate_summary_text(top_patterns, dominant_signal),
            "top_patterns": [
                {
                    "type": p.pattern_type.value,
                    "signal": p.signal.value,
                    "confidence": p.confidence,
                    "description": p.description,
                    "target_price": p.target_price,
                    "stop_loss": p.stop_loss,
                    "is_confirmed": p.is_confirmed,
                    "key_prices": p.key_prices,
                }
                for p in top_patterns
            ],
        }

    def _generate_summary_text(
        self,
        patterns: List[DetectedPattern],
        dominant_signal: str
    ) -> str:
        """生成摘要文字"""
        if not patterns:
            return "未檢測到明顯形態"

        signal_text = {
            "bullish": "看多",
            "bearish": "看空",
            "neutral": "觀望",
        }

        pattern_names = [p.description.split("：")[0] for p in patterns[:2]]

        return f"形態信號：{signal_text[dominant_signal]}｜檢測到 {', '.join(pattern_names)}"
