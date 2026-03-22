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
    THREE_WHITE_SOLDIERS = "three_white_soldiers"  # 三兵
    THREE_BLACK_CROWS = "three_black_crows"  # 三烏鴉
    ISLAND_REVERSAL = "island_reversal"  # 島型反轉
    BULLISH_ENGULFING = "bullish_engulfing"  # 看多吞噬
    BEARISH_ENGULFING = "bearish_engulfing"  # 看空吞噬
    DOJI = "doji"  # 十字星
    DRAGONFLY_DOJI = "dragonfly_doji"  # 蜻蜓十字星
    GRAVESTONE_DOJI = "gravestone_doji"  # 墓碑十字星
    HAMMER = "hammer"  # 槌子線
    INVERTED_HAMMER = "inverted_hammer"  # 倒槌子線
    MORNING_STAR = "morning_star"  # 晨星
    EVENING_STAR = "evening_star"  # 夜星
    BREAKAWAY_GAP = "breakaway_gap"  # 跳空缺口（突破型）
    RUNAWAY_GAP = "runaway_gap"  # 跳空缺口（逃竄型）
    EXHAUSTION_GAP = "exhaustion_gap"  # 跳空缺口（衰竭型）


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
        open_price = df_subset['open'].values

        patterns = []

        # 檢測各種形態
        patterns.extend(self._detect_head_shoulders(high, low, close))
        patterns.extend(self._detect_double_patterns(high, low, close))
        patterns.extend(self._detect_triangles(high, low, close))
        patterns.extend(self._detect_wedges(high, low, close))
        patterns.extend(self._detect_flags(high, low, close))
        patterns.extend(self._detect_breakouts(high, low, close))
        patterns.extend(self._detect_candlestick_patterns(open_price, high, low, close))
        patterns.extend(self._detect_gap_patterns(high, low, close))
        patterns.extend(self._detect_island_reversal(high, low, close))

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

    def _detect_candlestick_patterns(
        self,
        open_price: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """
        檢測蠟燭線形態
        包括：三兵、吞噬、十字星、槌子線、晨星、夜星
        """
        patterns = []

        if len(close) < 3:
            return patterns

        # 計算每根蠟燭的特徵
        body_size = np.abs(close - open_price)
        upper_wick = high - np.maximum(open_price, close)
        lower_wick = np.minimum(open_price, close) - low
        is_bullish = close > open_price
        is_bearish = close < open_price

        # 三兵形態（三根連續看漲蠟燭）
        patterns.extend(self._detect_three_soldiers(open_price, high, low, close, is_bullish, body_size))

        # 三烏鴉形態（三根連續看跌蠟燭）
        patterns.extend(self._detect_three_crows(open_price, high, low, close, is_bearish, body_size))

        # 吞噬形態
        patterns.extend(self._detect_engulfing(open_price, high, low, close, is_bullish, is_bearish, body_size))

        # 十字星形態
        patterns.extend(self._detect_doji_patterns(open_price, high, low, close, body_size, upper_wick, lower_wick))

        # 槌子線和倒槌子線
        patterns.extend(self._detect_hammer_patterns(open_price, high, low, close, body_size, upper_wick, lower_wick, is_bullish))

        # 晨星和夜星
        patterns.extend(self._detect_star_patterns(open_price, high, low, close, is_bullish, is_bearish, body_size))

        return patterns

    def _detect_three_soldiers(
        self,
        open_price: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        is_bullish: np.ndarray,
        body_size: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測三兵形態（三根連續上升的看漲蠟燭）"""
        patterns = []

        for i in range(len(close) - 2):
            # 檢查三根蠟燭都是看漲的，且開盤價在前一根蠟燭的上半部分
            if (is_bullish[i] and is_bullish[i+1] and is_bullish[i+2] and
                body_size[i] > 0.5 * (high[i] - low[i]) and  # 實體至少佔一半
                open_price[i+1] > close[i] - body_size[i] * 0.5 and  # 開盤在前一根上半部分
                open_price[i+2] > close[i+1] - body_size[i+1] * 0.5 and
                close[i+2] > close[i+1] > close[i]):  # 三根蠟燭逐漸上升

                confidence = 70
                target_price = close[-1] + (close[i+2] - open_price[i]) * 0.5
                stop_loss = low[i] * 0.98

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.THREE_WHITE_SOLDIERS,
                    signal=PatternSignal.BULLISH,
                    confidence=confidence,
                    start_index=i,
                    end_index=i + 2,
                    key_prices={
                        "first_candle_close": float(close[i]),
                        "second_candle_close": float(close[i+1]),
                        "third_candle_close": float(close[i+2]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"三兵形態：看多連續上升（{close[i]:.2f}-{close[i+2]:.2f}）",
                    is_confirmed=i + 2 == len(close) - 1,
                ))

        return patterns

    def _detect_three_crows(
        self,
        open_price: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        is_bearish: np.ndarray,
        body_size: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測三烏鴉形態（三根連續下降的看跌蠟燭）"""
        patterns = []

        for i in range(len(close) - 2):
            # 檢查三根蠟燭都是看跌的，且開盤價在前一根蠟燭的下半部分
            if (is_bearish[i] and is_bearish[i+1] and is_bearish[i+2] and
                body_size[i] > 0.5 * (high[i] - low[i]) and
                open_price[i+1] < close[i] + body_size[i] * 0.5 and
                open_price[i+2] < close[i+1] + body_size[i+1] * 0.5 and
                close[i+2] < close[i+1] < close[i]):  # 三根蠟燭逐漸下跌

                confidence = 70
                target_price = close[-1] - (open_price[i] - close[i+2]) * 0.5
                stop_loss = high[i] * 1.02

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.THREE_BLACK_CROWS,
                    signal=PatternSignal.BEARISH,
                    confidence=confidence,
                    start_index=i,
                    end_index=i + 2,
                    key_prices={
                        "first_candle_close": float(close[i]),
                        "second_candle_close": float(close[i+1]),
                        "third_candle_close": float(close[i+2]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"三烏鴉形態：看空連續下跌（{close[i]:.2f}-{close[i+2]:.2f}）",
                    is_confirmed=i + 2 == len(close) - 1,
                ))

        return patterns

    def _detect_engulfing(
        self,
        open_price: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        is_bullish: np.ndarray,
        is_bearish: np.ndarray,
        body_size: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測吞噬形態"""
        patterns = []

        for i in range(1, len(close)):
            # 看多吞噬：前一根是看跌，當前根看漲且完全吞噬
            if (is_bearish[i-1] and is_bullish[i] and
                open_price[i] <= close[i-1] and  # 當前開盤 <= 前一根收盤
                close[i] >= open_price[i-1]):  # 當前收盤 >= 前一根開盤

                confidence = 72
                target_price = close[i] + (close[i] - open_price[i]) * 1.5
                stop_loss = low[i] * 0.98

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.BULLISH_ENGULFING,
                    signal=PatternSignal.BULLISH,
                    confidence=confidence,
                    start_index=i - 1,
                    end_index=i,
                    key_prices={
                        "prev_candle_range": float(open_price[i-1] - close[i-1]),
                        "current_candle_body": float(close[i] - open_price[i]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"看多吞噬形態：{open_price[i]:.2f}-{close[i]:.2f}",
                    is_confirmed=i == len(close) - 1,
                ))

            # 看空吞噬：前一根是看漲，當前根看跌且完全吞噬
            elif (is_bullish[i-1] and is_bearish[i] and
                  open_price[i] >= close[i-1] and  # 當前開盤 >= 前一根收盤
                  close[i] <= open_price[i-1]):  # 當前收盤 <= 前一根開盤

                confidence = 72
                target_price = close[i] - (open_price[i] - close[i]) * 1.5
                stop_loss = high[i] * 1.02

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.BEARISH_ENGULFING,
                    signal=PatternSignal.BEARISH,
                    confidence=confidence,
                    start_index=i - 1,
                    end_index=i,
                    key_prices={
                        "prev_candle_range": float(close[i-1] - open_price[i-1]),
                        "current_candle_body": float(open_price[i] - close[i]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"看空吞噬形態：{open_price[i]:.2f}-{close[i]:.2f}",
                    is_confirmed=i == len(close) - 1,
                ))

        return patterns

    def _detect_doji_patterns(
        self,
        open_price: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        body_size: np.ndarray,
        upper_wick: np.ndarray,
        lower_wick: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測十字星形態（含蜻蜓和墓碑十字星）"""
        patterns = []

        for i in range(len(close)):
            body_range = high[i] - low[i]
            if body_range == 0:
                continue

            # 判斷是否為十字星（實體接近於0）
            body_pct = body_size[i] / body_range
            is_doji = body_pct < 0.1  # 實體小於全幅的 10%

            if is_doji:
                upper_pct = upper_wick[i] / body_range
                lower_pct = lower_wick[i] / body_range

                # 蜻蜓十字星（下影長，上影短）
                if lower_pct > upper_pct * 2 and lower_pct > 0.6:
                    confidence = 65
                    target_price = high[i] + (high[i] - low[i]) * 0.8
                    stop_loss = low[i] * 0.97

                    patterns.append(DetectedPattern(
                        pattern_type=PatternType.DRAGONFLY_DOJI,
                        signal=PatternSignal.BULLISH,
                        confidence=confidence,
                        start_index=i,
                        end_index=i,
                        key_prices={
                            "open": float(open_price[i]),
                            "high": float(high[i]),
                            "low": float(low[i]),
                            "close": float(close[i]),
                        },
                        target_price=float(target_price),
                        stop_loss=float(stop_loss),
                        description=f"蜻蜓十字星：{low[i]:.2f}-{high[i]:.2f}",
                        is_confirmed=False,
                    ))

                # 墓碑十字星（上影長，下影短）
                elif upper_pct > lower_pct * 2 and upper_pct > 0.6:
                    confidence = 65
                    target_price = low[i] - (high[i] - low[i]) * 0.8
                    stop_loss = high[i] * 1.03

                    patterns.append(DetectedPattern(
                        pattern_type=PatternType.GRAVESTONE_DOJI,
                        signal=PatternSignal.BEARISH,
                        confidence=confidence,
                        start_index=i,
                        end_index=i,
                        key_prices={
                            "open": float(open_price[i]),
                            "high": float(high[i]),
                            "low": float(low[i]),
                            "close": float(close[i]),
                        },
                        target_price=float(target_price),
                        stop_loss=float(stop_loss),
                        description=f"墓碑十字星：{low[i]:.2f}-{high[i]:.2f}",
                        is_confirmed=False,
                    ))

                # 普通十字星（上下影相近）
                elif abs(upper_pct - lower_pct) < 0.3:
                    confidence = 60
                    signal = PatternSignal.NEUTRAL
                    target_price = (high[i] + low[i]) / 2
                    stop_loss = low[i] * 0.97

                    patterns.append(DetectedPattern(
                        pattern_type=PatternType.DOJI,
                        signal=signal,
                        confidence=confidence,
                        start_index=i,
                        end_index=i,
                        key_prices={
                            "open": float(open_price[i]),
                            "high": float(high[i]),
                            "low": float(low[i]),
                            "close": float(close[i]),
                        },
                        target_price=float(target_price),
                        stop_loss=float(stop_loss),
                        description=f"十字星：關鍵反轉點位 {(high[i]+low[i])/2:.2f}",
                        is_confirmed=False,
                    ))

        return patterns

    def _detect_hammer_patterns(
        self,
        open_price: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        body_size: np.ndarray,
        upper_wick: np.ndarray,
        lower_wick: np.ndarray,
        is_bullish: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測槌子線和倒槌子線"""
        patterns = []

        for i in range(len(close)):
            body_range = high[i] - low[i]
            if body_range == 0:
                continue

            body_pct = body_size[i] / body_range
            lower_pct = lower_wick[i] / body_range
            upper_pct = upper_wick[i] / body_range

            # 槌子線：下影長（至少2倍實體），上影短，實體在高點附近
            if lower_pct > body_pct * 2 and lower_pct > 0.5 and upper_pct < body_pct:
                confidence = 68
                target_price = high[i] + (high[i] - low[i]) * 0.8
                stop_loss = low[i] * 0.97

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.HAMMER,
                    signal=PatternSignal.BULLISH,
                    confidence=confidence,
                    start_index=i,
                    end_index=i,
                    key_prices={
                        "open": float(open_price[i]),
                        "close": float(close[i]),
                        "high": float(high[i]),
                        "low": float(low[i]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"槌子線：潛在看多反轉 {close[i]:.2f}",
                    is_confirmed=False,
                ))

            # 倒槌子線（流星）：上影長，下影短，實體在低點附近
            elif upper_pct > body_pct * 2 and upper_pct > 0.5 and lower_pct < body_pct:
                confidence = 68
                target_price = low[i] - (high[i] - low[i]) * 0.8
                stop_loss = high[i] * 1.03

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.INVERTED_HAMMER,
                    signal=PatternSignal.BEARISH,
                    confidence=confidence,
                    start_index=i,
                    end_index=i,
                    key_prices={
                        "open": float(open_price[i]),
                        "close": float(close[i]),
                        "high": float(high[i]),
                        "low": float(low[i]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"倒槌子線：潛在看空反轉 {close[i]:.2f}",
                    is_confirmed=False,
                ))

        return patterns

    def _detect_star_patterns(
        self,
        open_price: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        is_bullish: np.ndarray,
        is_bearish: np.ndarray,
        body_size: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測晨星和夜星形態"""
        patterns = []

        if len(close) < 3:
            return patterns

        for i in range(1, len(close) - 1):
            # 晨星：看跌 -> 小實體 -> 看漲，且第三根能吞噬部分第一根
            if (is_bearish[i-1] and body_size[i] < body_size[i-1] * 0.5 and
                is_bullish[i+1] and close[i+1] > close[i-1] - body_size[i-1] * 0.5):

                confidence = 73
                target_price = high[i+1] + (high[i+1] - low[i]) * 0.5
                stop_loss = low[i] * 0.97

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.MORNING_STAR,
                    signal=PatternSignal.BULLISH,
                    confidence=confidence,
                    start_index=i - 1,
                    end_index=i + 1,
                    key_prices={
                        "first_candle_close": float(close[i-1]),
                        "middle_candle_body": float(body_size[i]),
                        "third_candle_close": float(close[i+1]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"晨星形態：看多反轉信號 {close[i+1]:.2f}",
                    is_confirmed=i + 1 == len(close) - 1,
                ))

            # 夜星：看漲 -> 小實體 -> 看跌，且第三根能吞噬部分第一根
            elif (is_bullish[i-1] and body_size[i] < body_size[i-1] * 0.5 and
                  is_bearish[i+1] and close[i+1] < close[i-1] + body_size[i-1] * 0.5):

                confidence = 73
                target_price = low[i+1] - (high[i] - low[i+1]) * 0.5
                stop_loss = high[i] * 1.03

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.EVENING_STAR,
                    signal=PatternSignal.BEARISH,
                    confidence=confidence,
                    start_index=i - 1,
                    end_index=i + 1,
                    key_prices={
                        "first_candle_close": float(close[i-1]),
                        "middle_candle_body": float(body_size[i]),
                        "third_candle_close": float(close[i+1]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"夜星形態：看空反轉信號 {close[i+1]:.2f}",
                    is_confirmed=i + 1 == len(close) - 1,
                ))

        return patterns

    def _detect_gap_patterns(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """
        檢測跳空缺口形態
        包括：突破型、逃竄型、衰竭型
        """
        patterns = []

        if len(close) < 5:
            return patterns

        for i in range(1, len(close)):
            gap_size = abs(low[i] - high[i-1])
            gap_pct = gap_size / high[i-1] if high[i-1] != 0 else 0

            # 有意義的缺口（至少 0.5% 的幅度）
            if gap_pct > 0.005:
                # 向上缺口
                if low[i] > high[i-1]:
                    recent_trend = close[i] - close[i-1] if i > 0 else 0
                    lookback_high = np.max(high[max(0, i-10):i-1])
                    lookback_low = np.min(low[max(0, i-10):i-1])
                    volume_trend = "增加" if i > 2 else "未知"

                    # 判斷缺口類型
                    if i > 10 and low[i] > lookback_high:
                        # 突破型缺口：缺口出現在關鍵阻力位之上
                        confidence = 72
                        gap_type = PatternType.BREAKAWAY_GAP
                        signal = PatternSignal.BULLISH
                        target_price = close[i] + gap_size * 2
                        description = f"突破型缺口：向上突破 {high[i-1]:.2f}"

                    elif i > 5 and i < len(close) - 5:
                        # 逃竄型缺口：趨勢中期出現
                        confidence = 70
                        gap_type = PatternType.RUNAWAY_GAP
                        signal = PatternSignal.BULLISH
                        target_price = close[i] + gap_size * 3
                        description = f"逃竄型缺口：向上延續 {close[i]:.2f}"

                    else:
                        continue

                    stop_loss = low[i] * 0.98

                    patterns.append(DetectedPattern(
                        pattern_type=gap_type,
                        signal=signal,
                        confidence=confidence,
                        start_index=i - 1,
                        end_index=i,
                        key_prices={
                            "prev_high": float(high[i-1]),
                            "current_low": float(low[i]),
                            "gap_size": float(gap_size),
                            "gap_pct": float(gap_pct * 100),
                        },
                        target_price=float(target_price),
                        stop_loss=float(stop_loss),
                        description=description,
                        is_confirmed=True,
                    ))

                # 向下缺口
                else:
                    lookback_high = np.max(high[max(0, i-10):i-1])
                    lookback_low = np.min(low[max(0, i-10):i-1])

                    # 判斷缺口類型
                    if i > 10 and high[i] < lookback_low:
                        # 突破型缺口：缺口出現在關鍵支撐位之下
                        confidence = 72
                        gap_type = PatternType.BREAKAWAY_GAP
                        signal = PatternSignal.BEARISH
                        target_price = close[i] - gap_size * 2
                        description = f"突破型缺口：向下突破 {low[i-1]:.2f}"

                    elif i > 5 and i < len(close) - 5:
                        # 逃竄型缺口：趨勢中期出現
                        confidence = 70
                        gap_type = PatternType.RUNAWAY_GAP
                        signal = PatternSignal.BEARISH
                        target_price = close[i] - gap_size * 3
                        description = f"逃竄型缺口：向下延續 {close[i]:.2f}"

                    else:
                        continue

                    stop_loss = high[i] * 1.02

                    patterns.append(DetectedPattern(
                        pattern_type=gap_type,
                        signal=signal,
                        confidence=confidence,
                        start_index=i - 1,
                        end_index=i,
                        key_prices={
                            "prev_low": float(low[i-1]),
                            "current_high": float(high[i]),
                            "gap_size": float(gap_size),
                            "gap_pct": float(gap_pct * 100),
                        },
                        target_price=float(target_price),
                        stop_loss=float(stop_loss),
                        description=description,
                        is_confirmed=True,
                    ))

        return patterns

    def _detect_island_reversal(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> List[DetectedPattern]:
        """檢測島型反轉形態"""
        patterns = []

        if len(close) < 5:
            return patterns

        # 尋找兩個方向相反的缺口
        for i in range(2, len(close) - 1):
            # 向上缺口後又向下缺口（看空島型反轉）
            if (low[i] > high[i-2] and high[i+1] < low[i]):
                island_high = np.max(high[i-1:i+1])
                island_low = np.min(low[i-1:i+1])
                gap_distance = (low[i] - high[i-2]) + (low[i] - high[i+1])

                confidence = 75
                target_price = close[-1] - gap_distance * 1.5
                stop_loss = island_high * 1.02

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.ISLAND_REVERSAL,
                    signal=PatternSignal.BEARISH,
                    confidence=confidence,
                    start_index=i - 2,
                    end_index=i + 1,
                    key_prices={
                        "island_high": float(island_high),
                        "island_low": float(island_low),
                        "entry_gap": float(low[i] - high[i-2]),
                        "exit_gap": float(low[i] - high[i+1]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"看空島型反轉：高點 {island_high:.2f}",
                    is_confirmed=True,
                ))

            # 向下缺口後又向上缺口（看多島型反轉）
            elif (high[i] < low[i-2] and low[i+1] > high[i]):
                island_high = np.max(high[i-1:i+1])
                island_low = np.min(low[i-1:i+1])
                gap_distance = (low[i-2] - high[i]) + (low[i+1] - high[i])

                confidence = 75
                target_price = close[-1] + gap_distance * 1.5
                stop_loss = island_low * 0.98

                patterns.append(DetectedPattern(
                    pattern_type=PatternType.ISLAND_REVERSAL,
                    signal=PatternSignal.BULLISH,
                    confidence=confidence,
                    start_index=i - 2,
                    end_index=i + 1,
                    key_prices={
                        "island_high": float(island_high),
                        "island_low": float(island_low),
                        "entry_gap": float(low[i-2] - high[i]),
                        "exit_gap": float(low[i+1] - high[i]),
                    },
                    target_price=float(target_price),
                    stop_loss=float(stop_loss),
                    description=f"看多島型反轉：低點 {island_low:.2f}",
                    is_confirmed=True,
                ))

        return patterns

    def get_ai_pattern_summary(
        self,
        patterns: List[DetectedPattern]
    ) -> Dict:
        """
        生成適合 AI 分析的形態摘要

        包含：
        - 整體形態偏向（看多/看空/中性）
        - 最強信號形態
        - 衝突信號檢測
        - 根據形態匯聚的建議行動
        """
        if not patterns:
            return {
                "overall_bias": "neutral",
                "confidence_level": 0,
                "strongest_pattern": None,
                "conflicting_signals": False,
                "signal_count": {"bullish": 0, "bearish": 0, "neutral": 0},
                "confluence_score": 0,
                "recommended_action": "等待更多確認信號",
                "risk_level": "低",
            }

        # 統計信號
        bullish_patterns = [p for p in patterns if p.signal == PatternSignal.BULLISH]
        bearish_patterns = [p for p in patterns if p.signal == PatternSignal.BEARISH]
        neutral_patterns = [p for p in patterns if p.signal == PatternSignal.NEUTRAL]

        bullish_score = sum(p.confidence for p in bullish_patterns)
        bearish_score = sum(p.confidence for p in bearish_patterns)

        # 判斷整體偏向
        if bullish_score > bearish_score * 1.3:
            overall_bias = "bullish"
            bias_strength = "強"
        elif bearish_score > bullish_score * 1.3:
            overall_bias = "bearish"
            bias_strength = "強"
        else:
            overall_bias = "neutral"
            bias_strength = "弱"

        # 找出最強信號
        strongest_pattern = max(patterns, key=lambda x: x.confidence) if patterns else None

        # 檢測衝突信號
        conflicting_signals = (len(bullish_patterns) > 0 and len(bearish_patterns) > 0 and
                              abs(bullish_score - bearish_score) < bullish_score * 0.3)

        # 計算形態匯聚分數（0-100）
        confluence_score = self._calculate_confluence_score(patterns)

        # 生成建議行動
        recommended_action = self._generate_recommended_action(
            overall_bias, confluence_score, conflicting_signals, patterns
        )

        # 判斷風險等級
        if confluence_score < 40:
            risk_level = "高"
        elif confluence_score < 60:
            risk_level = "中"
        else:
            risk_level = "低"

        return {
            "overall_bias": overall_bias,
            "bias_strength": bias_strength,
            "confidence_level": min(100, (bullish_score + bearish_score) / 2),
            "strongest_pattern": {
                "type": strongest_pattern.pattern_type.value,
                "confidence": strongest_pattern.confidence,
                "signal": strongest_pattern.signal.value,
                "description": strongest_pattern.description,
            } if strongest_pattern else None,
            "conflicting_signals": conflicting_signals,
            "signal_count": {
                "bullish": len(bullish_patterns),
                "bearish": len(bearish_patterns),
                "neutral": len(neutral_patterns),
            },
            "signal_scores": {
                "bullish": float(bullish_score),
                "bearish": float(bearish_score),
            },
            "confluence_score": confluence_score,
            "recommended_action": recommended_action,
            "risk_level": risk_level,
            "top_3_patterns": [
                {
                    "type": p.pattern_type.value,
                    "confidence": p.confidence,
                    "signal": p.signal.value,
                    "target": p.target_price,
                    "stop_loss": p.stop_loss,
                }
                for p in patterns[:3]
            ],
        }

    def _calculate_confluence_score(self, patterns: List[DetectedPattern]) -> float:
        """
        計算形態匯聚分數
        多個同向信號會提高分數
        """
        if not patterns:
            return 0

        # 根據信號方向分組
        bullish_patterns = [p for p in patterns if p.signal == PatternSignal.BULLISH]
        bearish_patterns = [p for p in patterns if p.signal == PatternSignal.BEARISH]

        bullish_count = len(bullish_patterns)
        bearish_count = len(bearish_patterns)

        # 計算信心度加權
        bullish_weighted = sum(p.confidence for p in bullish_patterns) / max(bullish_count, 1)
        bearish_weighted = sum(p.confidence for p in bearish_patterns) / max(bearish_count, 1)

        # 匯聚分數基於：信號數量和信心度
        confluence_base = max(bullish_weighted, bearish_weighted)

        # 同向信號數量加分
        dominant_count = max(bullish_count, bearish_count)
        if dominant_count >= 3:
            confluence_bonus = 15
        elif dominant_count == 2:
            confluence_bonus = 8
        else:
            confluence_bonus = 0

        # 已確認的形態加分
        confirmed_count = sum(1 for p in patterns if p.is_confirmed)
        confirmation_bonus = min(20, confirmed_count * 5)

        confluence_score = min(100, confluence_base + confluence_bonus + confirmation_bonus)
        return confluence_score

    def _generate_recommended_action(
        self,
        overall_bias: str,
        confluence_score: float,
        conflicting_signals: bool,
        patterns: List[DetectedPattern]
    ) -> str:
        """根據形態分析生成建議行動"""
        if conflicting_signals:
            return "信號衝突，建議觀望或分批進場"

        if confluence_score < 40:
            return "信號較弱，建議等待確認"
        elif confluence_score < 60:
            return "信號中等，可考慮輕倉試探"
        else:
            action_prefix = "強烈看多，建議逢低買進" if overall_bias == "bullish" else "強烈看空，建議逢高賣出" if overall_bias == "bearish" else "信號中性，建議謹慎交易"

            # 加上目標和停損
            if patterns:
                top_pattern = max(patterns, key=lambda x: x.confidence)
                if top_pattern.target_price and top_pattern.stop_loss:
                    return f"{action_prefix}｜目標：{top_pattern.target_price:.2f}｜停損：{top_pattern.stop_loss:.2f}"

            return action_prefix

    def find_support_resistance_levels(
        self,
        df: pd.DataFrame,
        lookback: int = 60
    ) -> Dict:
        """
        識別關鍵支撐和阻力位

        Returns:
            {
                "support_levels": [...],
                "resistance_levels": [...],
                "key_levels": [...],
            }
        """
        if len(df) < lookback:
            lookback = len(df)

        df_subset = df.tail(lookback).copy()
        high = df_subset['high'].values
        low = df_subset['low'].values
        close = df_subset['close'].values

        # 尋找局部極值
        max_idx, min_idx = self.find_local_extrema(high, order=3)

        # 提取支撐和阻力位
        resistance_levels = sorted(high[max_idx], reverse=True) if len(max_idx) > 0 else []
        support_levels = sorted(low[min_idx]) if len(min_idx) > 0 else []

        # 聚類相近的價位（容差 1%）
        resistance_levels = self._cluster_price_levels(resistance_levels)
        support_levels = self._cluster_price_levels(support_levels)

        # 找出最強關鍵位（出現頻率最高或最新的）
        current_price = close[-1]
        nearest_resistance = min([r for r in resistance_levels if r > current_price],
                                default=max(resistance_levels) if resistance_levels else current_price)
        nearest_support = max([s for s in support_levels if s < current_price],
                             default=min(support_levels) if support_levels else current_price)

        return {
            "support_levels": [float(s) for s in support_levels],
            "resistance_levels": [float(r) for r in resistance_levels],
            "nearest_support": float(nearest_support),
            "nearest_resistance": float(nearest_resistance),
            "current_price": float(current_price),
            "support_count": len(support_levels),
            "resistance_count": len(resistance_levels),
        }

    def _cluster_price_levels(self, levels: List[float], tolerance_pct: float = 0.01) -> List[float]:
        """
        聚類相近的價格位
        容差：1%
        """
        if not levels:
            return []

        levels = sorted(levels, reverse=True)
        clustered = []
        current_cluster = [levels[0]]

        for level in levels[1:]:
            # 檢查是否在容差範圍內
            if abs(level - current_cluster[0]) / current_cluster[0] < tolerance_pct:
                current_cluster.append(level)
            else:
                # 保存當前聚類的平均值
                clustered.append(np.mean(current_cluster))
                current_cluster = [level]

        # 保存最後的聚類
        if current_cluster:
            clustered.append(np.mean(current_cluster))

        return sorted(clustered, reverse=True)
