"""
策略回測引擎 — 支援多種技術指標策略的歷史回測
"""
import logging
import math
from datetime import datetime
from typing import Dict, List, Any, Optional

import pandas as pd
import numpy as np

from app.services.technical_indicators import TechnicalIndicators

logger = logging.getLogger(__name__)

# 可用策略定義
STRATEGIES = {
    "ma_crossover": {
        "name": "ma_crossover",
        "display_name": "均線交叉",
        "description": "短期均線上穿長期均線時買入，下穿時賣出",
        "default_params": {"short_period": 5, "long_period": 20},
    },
    "rsi": {
        "name": "rsi",
        "display_name": "RSI 超買超賣",
        "description": "RSI 低於超賣線時買入，高於超買線時賣出",
        "default_params": {"period": 14, "oversold": 30, "overbought": 70},
    },
    "macd": {
        "name": "macd",
        "display_name": "MACD 信號交叉",
        "description": "MACD 線上穿信號線時買入，下穿時賣出",
        "default_params": {"fast": 12, "slow": 26, "signal": 9},
    },
    "bollinger_bands": {
        "name": "bollinger_bands",
        "display_name": "布林通道均值回歸",
        "description": "價格觸及下軌時買入，觸及上軌時賣出",
        "default_params": {"period": 20, "std_dev": 2.0},
    },
    "kd_crossover": {
        "name": "kd_crossover",
        "display_name": "KD 指標交叉",
        "description": "K 值上穿 D 值且處於低檔時買入，K 值下穿 D 值且處於高檔時賣出",
        "default_params": {"period": 9, "oversold": 20, "overbought": 80},
    },
    "ma_deduction": {
        "name": "ma_deduction",
        "display_name": "均線扣抵策略",
        "description": "多條短期均線扣抵於長期均線時買入，均線負離過大時賣出",
        "default_params": {"short_period": 5, "mid_period": 10, "long_period": 30},
    },
    "chip_analysis": {
        "name": "chip_analysis",
        "display_name": "籌碼面策略",
        "description": "基於大宗交易的機構買賣信號，機構大買時買入，機構大賣時賣出",
        "default_params": {"volume_threshold": 2.0},  # 交易量倍數
    },
    "momentum": {
        "name": "momentum",
        "display_name": "動量策略",
        "description": "基於價格變化率 (ROC)，正動量時買入，負動量時賣出",
        "default_params": {"period": 10, "threshold": 0.0},
    },
    "channel_breakout": {
        "name": "channel_breakout",
        "display_name": "通道突破策略",
        "description": "基於 Donchian 通道，價格突破上軌時買入，跌破下軌時賣出",
        "default_params": {"period": 20},
    },
    "mean_reversion": {
        "name": "mean_reversion",
        "display_name": "均值回歸策略",
        "description": "價格超賣時買入，超買時賣出，預期價格回歸均值",
        "default_params": {"period": 20, "std_dev": 2.0, "zscore_threshold": 1.5},
    },
}


class StrategyBacktestEngine:
    """策略回測引擎"""

    def __init__(self):
        self.ti = TechnicalIndicators()

    def run_backtest(
        self,
        history: List[dict],
        strategy: str,
        params: Dict[str, Any],
        initial_capital: float = 1_000_000,
    ) -> Dict[str, Any]:
        """
        執行策略回測

        Args:
            history: 歷史 OHLCV 資料 [{date, open, high, low, close, volume}, ...]
            strategy: 策略名稱
            params: 策略參數
            initial_capital: 初始資金

        Returns:
            回測結果 (metrics, equity_curve, trades, signals)
        """
        if strategy not in STRATEGIES:
            raise ValueError(f"不支援的策略: {strategy}")

        # 合併預設參數
        merged_params = {**STRATEGIES[strategy]["default_params"], **params}

        # 轉為 DataFrame
        df = pd.DataFrame(history)
        if df.empty or len(df) < 30:
            raise ValueError("歷史資料不足，至少需要 30 筆")

        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # 產生信號
        signals = self._generate_signals(df, strategy, merged_params)

        # 模擬交易
        trades, equity_curve = self._simulate_trades(
            df, signals, initial_capital
        )

        # 計算績效
        metrics = self._calculate_metrics(
            trades, equity_curve, initial_capital
        )

        return {
            "strategy": strategy,
            "params": merged_params,
            "metrics": metrics,
            "equity_curve": equity_curve,
            "trades": trades,
            "signals": signals,
        }

    # ---- 信號產生 ----

    def _generate_signals(
        self, df: pd.DataFrame, strategy: str, params: dict
    ) -> List[dict]:
        """根據策略產生買賣信號"""
        method = getattr(self, f"_signals_{strategy}")
        return method(df, params)

    def _signals_ma_crossover(self, df: pd.DataFrame, p: dict) -> List[dict]:
        short_ma = self.ti.calculate_ma(df["close"], p["short_period"])
        long_ma = self.ti.calculate_ma(df["close"], p["long_period"])
        signals = []

        for i in range(1, len(df)):
            if pd.isna(short_ma.iloc[i]) or pd.isna(long_ma.iloc[i]):
                continue
            if pd.isna(short_ma.iloc[i - 1]) or pd.isna(long_ma.iloc[i - 1]):
                continue

            # 黃金交叉：短均線從下方穿越長均線
            if short_ma.iloc[i - 1] <= long_ma.iloc[i - 1] and short_ma.iloc[i] > long_ma.iloc[i]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"MA{p['short_period']}={short_ma.iloc[i]:.2f}, MA{p['long_period']}={long_ma.iloc[i]:.2f}",
                })
            # 死亡交叉：短均線從上方穿越長均線
            elif short_ma.iloc[i - 1] >= long_ma.iloc[i - 1] and short_ma.iloc[i] < long_ma.iloc[i]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"MA{p['short_period']}={short_ma.iloc[i]:.2f}, MA{p['long_period']}={long_ma.iloc[i]:.2f}",
                })

        return signals

    def _signals_rsi(self, df: pd.DataFrame, p: dict) -> List[dict]:
        rsi = self.ti.calculate_rsi(df["close"], p["period"])
        signals = []

        for i in range(1, len(df)):
            if pd.isna(rsi.iloc[i]) or pd.isna(rsi.iloc[i - 1]):
                continue

            # RSI 從超賣區上穿
            if rsi.iloc[i - 1] < p["oversold"] and rsi.iloc[i] >= p["oversold"]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"RSI={rsi.iloc[i]:.2f}",
                })
            # RSI 從超買區下穿
            elif rsi.iloc[i - 1] > p["overbought"] and rsi.iloc[i] <= p["overbought"]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"RSI={rsi.iloc[i]:.2f}",
                })

        return signals

    def _signals_macd(self, df: pd.DataFrame, p: dict) -> List[dict]:
        macd_data = self.ti.calculate_macd(df["close"], p["fast"], p["slow"], p["signal"])
        macd_line = macd_data["macd"]
        signal_line = macd_data["signal"]
        signals = []

        for i in range(1, len(df)):
            if pd.isna(macd_line.iloc[i]) or pd.isna(signal_line.iloc[i]):
                continue
            if pd.isna(macd_line.iloc[i - 1]) or pd.isna(signal_line.iloc[i - 1]):
                continue

            # MACD 上穿信號線
            if macd_line.iloc[i - 1] <= signal_line.iloc[i - 1] and macd_line.iloc[i] > signal_line.iloc[i]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"MACD={macd_line.iloc[i]:.2f}, Signal={signal_line.iloc[i]:.2f}",
                })
            # MACD 下穿信號線
            elif macd_line.iloc[i - 1] >= signal_line.iloc[i - 1] and macd_line.iloc[i] < signal_line.iloc[i]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"MACD={macd_line.iloc[i]:.2f}, Signal={signal_line.iloc[i]:.2f}",
                })

        return signals

    def _signals_bollinger_bands(self, df: pd.DataFrame, p: dict) -> List[dict]:
        bb = self.ti.calculate_bollinger_bands(df["close"], p["period"], p["std_dev"])
        signals = []

        for i in range(1, len(df)):
            if pd.isna(bb["upper"].iloc[i]) or pd.isna(bb["lower"].iloc[i]):
                continue

            close = df["close"].iloc[i]
            prev_close = df["close"].iloc[i - 1]

            # 價格從下方觸碰或穿越下軌後回升
            if prev_close <= bb["lower"].iloc[i - 1] and close > bb["lower"].iloc[i]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(close),
                    "indicator_value": f"Lower={bb['lower'].iloc[i]:.2f}, Middle={bb['middle'].iloc[i]:.2f}, Upper={bb['upper'].iloc[i]:.2f}",
                })
            # 價格從上方觸碰或穿越上軌後回落
            elif prev_close >= bb["upper"].iloc[i - 1] and close < bb["upper"].iloc[i]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(close),
                    "indicator_value": f"Lower={bb['lower'].iloc[i]:.2f}, Middle={bb['middle'].iloc[i]:.2f}, Upper={bb['upper'].iloc[i]:.2f}",
                })

        return signals

    def _signals_kd_crossover(self, df: pd.DataFrame, p: dict) -> List[dict]:
        kd = self.ti.calculate_kd(df["high"], df["low"], df["close"], p["period"])
        k_line = kd["k"]
        d_line = kd["d"]
        signals = []

        for i in range(1, len(df)):
            if pd.isna(k_line.iloc[i]) or pd.isna(d_line.iloc[i]):
                continue
            if pd.isna(k_line.iloc[i - 1]) or pd.isna(d_line.iloc[i - 1]):
                continue

            # K 上穿 D 且處於低檔區
            if (k_line.iloc[i - 1] <= d_line.iloc[i - 1]
                    and k_line.iloc[i] > d_line.iloc[i]
                    and k_line.iloc[i] < p["overbought"]):
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"K={k_line.iloc[i]:.2f}, D={d_line.iloc[i]:.2f}",
                })
            # K 下穿 D 且處於高檔區
            elif (k_line.iloc[i - 1] >= d_line.iloc[i - 1]
                  and k_line.iloc[i] < d_line.iloc[i]
                  and k_line.iloc[i] > p["oversold"]):
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"K={k_line.iloc[i]:.2f}, D={d_line.iloc[i]:.2f}",
                })

        return signals

    def _signals_ma_deduction(self, df: pd.DataFrame, p: dict) -> List[dict]:
        """均線扣抵策略：多條短期均線同時低於長期均線時買入"""
        short_ma = self.ti.calculate_ma(df["close"], p["short_period"])
        mid_ma = self.ti.calculate_ma(df["close"], p["mid_period"])
        long_ma = self.ti.calculate_ma(df["close"], p["long_period"])
        signals = []
        in_position = False

        for i in range(1, len(df)):
            if pd.isna(short_ma.iloc[i]) or pd.isna(mid_ma.iloc[i]) or pd.isna(long_ma.iloc[i]):
                continue

            # 買入信號：短期均線和中期均線都低於長期均線，且價格上升
            short_below = short_ma.iloc[i] < long_ma.iloc[i]
            mid_below = mid_ma.iloc[i] < long_ma.iloc[i]
            price_above_short = df["close"].iloc[i] > short_ma.iloc[i]

            if short_below and mid_below and price_above_short and not in_position:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"MA{p['short_period']}={short_ma.iloc[i]:.2f}, MA{p['mid_period']}={mid_ma.iloc[i]:.2f}, MA{p['long_period']}={long_ma.iloc[i]:.2f}",
                })
                in_position = True

            # 賣出信號：短期均線上穿長期均線，或價格跌回短期均線
            elif in_position and (short_ma.iloc[i] > long_ma.iloc[i] or df["close"].iloc[i] < short_ma.iloc[i]):
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"MA{p['short_period']}={short_ma.iloc[i]:.2f}, MA{p['mid_period']}={mid_ma.iloc[i]:.2f}, MA{p['long_period']}={long_ma.iloc[i]:.2f}",
                })
                in_position = False

        return signals

    def _signals_chip_analysis(self, df: pd.DataFrame, p: dict) -> List[dict]:
        """籌碼面策略：基於成交量異常偵測機構買賣"""
        signals = []
        avg_volume = df["volume"].rolling(window=20).mean()
        in_position = False

        for i in range(20, len(df)):
            if pd.isna(avg_volume.iloc[i]):
                continue

            # 異常成交量倍數
            volume_ratio = df["volume"].iloc[i] / avg_volume.iloc[i]

            # 買入信號：成交量暴增（機構大買）且價格上升
            if volume_ratio > p["volume_threshold"] and df["close"].iloc[i] > df["close"].iloc[i - 1] and not in_position:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"Volume Ratio={volume_ratio:.2f}x, Volume={df['volume'].iloc[i]:.0f}",
                })
                in_position = True

            # 賣出信號：成交量暴增但價格下跌（機構大賣）
            elif in_position and volume_ratio > p["volume_threshold"] and df["close"].iloc[i] < df["close"].iloc[i - 1]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"Volume Ratio={volume_ratio:.2f}x, Volume={df['volume'].iloc[i]:.0f}",
                })
                in_position = False

        return signals

    def _signals_momentum(self, df: pd.DataFrame, p: dict) -> List[dict]:
        """動量策略：基於價格變化率 (ROC)"""
        signals = []
        roc = self._calculate_roc(df["close"], p["period"])

        for i in range(1, len(df)):
            if pd.isna(roc.iloc[i]) or pd.isna(roc.iloc[i - 1]):
                continue

            # 買入信號：動量從負轉正（價格開始加速上升）
            if roc.iloc[i - 1] <= p["threshold"] and roc.iloc[i] > p["threshold"]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"ROC={roc.iloc[i]:.2f}%",
                })

            # 賣出信號：動量從正轉負（價格開始減速）
            elif roc.iloc[i - 1] >= p["threshold"] and roc.iloc[i] < p["threshold"]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"ROC={roc.iloc[i]:.2f}%",
                })

        return signals

    def _signals_channel_breakout(self, df: pd.DataFrame, p: dict) -> List[dict]:
        """通道突破策略：Donchian 通道"""
        signals = []
        high_channel = df["high"].rolling(window=p["period"]).max()
        low_channel = df["low"].rolling(window=p["period"]).min()

        for i in range(p["period"], len(df)):
            if pd.isna(high_channel.iloc[i]) or pd.isna(low_channel.iloc[i]):
                continue

            # 買入信號：價格突破上軌
            if df["close"].iloc[i] > high_channel.iloc[i - 1] and df["close"].iloc[i - 1] <= high_channel.iloc[i - 1]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"Upper Channel={high_channel.iloc[i]:.2f}, Lower Channel={low_channel.iloc[i]:.2f}",
                })

            # 賣出信號：價格跌破下軌
            elif df["close"].iloc[i] < low_channel.iloc[i - 1] and df["close"].iloc[i - 1] >= low_channel.iloc[i - 1]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"Upper Channel={high_channel.iloc[i]:.2f}, Lower Channel={low_channel.iloc[i]:.2f}",
                })

        return signals

    def _signals_mean_reversion(self, df: pd.DataFrame, p: dict) -> List[dict]:
        """均值回歸策略：基於 Z-Score 的超買超賣"""
        signals = []
        ma = self.ti.calculate_ma(df["close"], p["period"])
        std = df["close"].rolling(window=p["period"]).std()

        for i in range(p["period"], len(df)):
            if pd.isna(ma.iloc[i]) or pd.isna(std.iloc[i]) or std.iloc[i] == 0:
                continue

            # 計算 Z-Score
            zscore = (df["close"].iloc[i] - ma.iloc[i]) / std.iloc[i]

            # 買入信號：Z-Score < -1.5（超賣，預期反彈）
            if zscore < -p["zscore_threshold"]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "BUY",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"Z-Score={zscore:.2f}, MA={ma.iloc[i]:.2f}",
                })

            # 賣出信號：Z-Score > 1.5（超買，預期回調）
            elif zscore > p["zscore_threshold"]:
                signals.append({
                    "date": df["date"].iloc[i],
                    "signal": "SELL",
                    "price": float(df["close"].iloc[i]),
                    "indicator_value": f"Z-Score={zscore:.2f}, MA={ma.iloc[i]:.2f}",
                })

        return signals

    # ---- 模擬交易 ----

    def _simulate_trades(
        self,
        df: pd.DataFrame,
        signals: List[dict],
        initial_capital: float,
    ) -> tuple:
        """模擬交易，產生交易紀錄與權益曲線"""
        capital = initial_capital
        position = 0  # 持有股數
        entry_price = 0.0
        entry_date = ""
        trades = []

        # 建立日期→信號的快速查找
        signal_map: Dict[str, str] = {}
        for s in signals:
            signal_map[s["date"]] = s["signal"]

        equity_curve = []
        buy_hold_value = initial_capital  # 買賣持有策略的權益值

        for i in range(len(df)):
            date_str = df["date"].iloc[i]
            close = float(df["close"].iloc[i])
            sig = signal_map.get(date_str)

            if sig == "BUY" and position == 0:
                # 全倉買入（以收盤價買入，扣除手續費 0.1425%）
                fee_rate = 0.001425
                max_shares = int(capital / (close * (1 + fee_rate)))
                if max_shares > 0:
                    cost = max_shares * close * (1 + fee_rate)
                    capital -= cost
                    position = max_shares
                    entry_price = close
                    entry_date = date_str

            elif sig == "SELL" and position > 0:
                # 全部賣出（手續費 0.1425% + 證交稅 0.3%）
                fee_rate = 0.001425
                tax_rate = 0.003
                revenue = position * close * (1 - fee_rate - tax_rate)
                pnl = revenue - (position * entry_price * (1 + 0.001425))
                return_pct = (close - entry_price) / entry_price * 100

                # 計算持倉天數
                try:
                    d1 = datetime.strptime(entry_date, "%Y-%m-%d")
                    d2 = datetime.strptime(date_str, "%Y-%m-%d")
                    holding_days = (d2 - d1).days
                except ValueError:
                    holding_days = 0

                trades.append({
                    "entry_date": entry_date,
                    "entry_price": entry_price,
                    "exit_date": date_str,
                    "exit_price": close,
                    "shares": position,
                    "pnl": round(pnl, 2),
                    "return_pct": round(return_pct, 2),
                    "holding_days": holding_days,
                })

                capital += revenue
                position = 0
                entry_price = 0.0
                entry_date = ""

            # 當前權益 = 現金 + 持倉市值
            equity = capital + position * close

            # 買賣持有基準值（第一個非零價格後開始計算）
            if i == 0:
                initial_price = close
            if i > 0:
                buy_hold_value = initial_capital * (close / initial_price)

            equity_curve.append({
                "date": date_str,
                "equity": round(equity, 2),
                "drawdown": 0.0,  # 之後計算
                "daily_return": 0.0,  # 之後計算
                "buy_hold_value": round(buy_hold_value, 2),
            })

        # 計算回撤、日報酬率
        if equity_curve:
            peak = equity_curve[0]["equity"]
            for i, point in enumerate(equity_curve):
                if point["equity"] > peak:
                    peak = point["equity"]
                dd = (peak - point["equity"]) / peak * 100 if peak > 0 else 0
                point["drawdown"] = round(dd, 2)

                # 計算日報酬率
                if i > 0:
                    prev_equity = equity_curve[i - 1]["equity"]
                    daily_return = (point["equity"] - prev_equity) / prev_equity * 100 if prev_equity > 0 else 0
                    point["daily_return"] = round(daily_return, 2)

        return trades, equity_curve

    # ---- 績效計算 ----

    def _calculate_metrics(
        self,
        trades: List[dict],
        equity_curve: List[dict],
        initial_capital: float,
    ) -> dict:
        """計算績效指標，包含進階指標"""
        if not equity_curve:
            return self._empty_metrics()

        final_equity = equity_curve[-1]["equity"]
        total_return = (final_equity - initial_capital) / initial_capital * 100

        # 年化報酬率
        if len(equity_curve) >= 2:
            try:
                d1 = datetime.strptime(equity_curve[0]["date"], "%Y-%m-%d")
                d2 = datetime.strptime(equity_curve[-1]["date"], "%Y-%m-%d")
                years = (d2 - d1).days / 365.25
                if years > 0:
                    annualized = ((final_equity / initial_capital) ** (1 / years) - 1) * 100
                else:
                    annualized = 0
            except (ValueError, ZeroDivisionError):
                annualized = 0
        else:
            annualized = 0

        # 最大回撤與回撤相關指標
        max_drawdown = max((p["drawdown"] for p in equity_curve), default=0)

        # 買賣持有報酬率（基準比較）
        if equity_curve:
            buy_hold_final = equity_curve[-1].get("buy_hold_value", initial_capital)
            buy_hold_return = (buy_hold_final - initial_capital) / initial_capital * 100
        else:
            buy_hold_return = 0

        # 交易統計
        total_trades = len(trades)
        if total_trades > 0:
            winning = [t for t in trades if t["pnl"] > 0]
            losing = [t for t in trades if t["pnl"] < 0]
            win_rate = len(winning) / total_trades * 100
            avg_holding = sum(t["holding_days"] for t in trades) / total_trades

            total_gains = sum(t["pnl"] for t in winning)
            total_losses = abs(sum(t["pnl"] for t in losing))
            profit_factor = total_gains / total_losses if total_losses > 0 else float("inf")

            # 最佳與最差交易
            best_trade = max(trades, key=lambda t: t["pnl"])
            worst_trade = min(trades, key=lambda t: t["pnl"])
            best_trade_pnl = best_trade["pnl"]
            worst_trade_pnl = worst_trade["pnl"]

            # 連勝連敗統計
            win_streak, loss_streak = self._calculate_win_loss_streak(trades)

            # 月份報酬率
            monthly_returns = self._calculate_monthly_returns(equity_curve)
            monthly_win_rate = self._calculate_monthly_win_rate(monthly_returns)
        else:
            win_rate = 0
            avg_holding = 0
            profit_factor = 0
            best_trade_pnl = 0
            worst_trade_pnl = 0
            win_streak = 0
            loss_streak = 0
            monthly_win_rate = 0

        # Sharpe Ratio（日報酬率計算）
        sharpe = self._calculate_sharpe(equity_curve)

        # Sortino Ratio（只考慮下檔波動）
        sortino = self._calculate_sortino(equity_curve)

        # Calmar Ratio
        calmar = self._calculate_calmar(annualized, max_drawdown)

        return {
            "total_return": round(total_return, 2),
            "annualized_return": round(annualized, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "sortino_ratio": round(sortino, 2),
            "calmar_ratio": round(calmar, 2),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else 999.99,
            "total_trades": total_trades,
            "avg_holding_days": round(avg_holding, 1),
            "best_trade_pnl": round(best_trade_pnl, 2) if total_trades > 0 else 0,
            "worst_trade_pnl": round(worst_trade_pnl, 2) if total_trades > 0 else 0,
            "consecutive_wins": win_streak,
            "consecutive_losses": loss_streak,
            "monthly_win_rate": round(monthly_win_rate, 2),
            "buy_hold_return": round(buy_hold_return, 2),
        }

    def _calculate_sharpe(self, equity_curve: List[dict], risk_free_rate: float = 0.02) -> float:
        """計算年化 Sharpe Ratio"""
        if len(equity_curve) < 2:
            return 0.0

        equities = [p["equity"] for p in equity_curve]
        returns = []
        for i in range(1, len(equities)):
            if equities[i - 1] > 0:
                returns.append((equities[i] - equities[i - 1]) / equities[i - 1])

        if not returns:
            return 0.0

        arr = np.array(returns)
        mean_r = np.mean(arr)
        std_r = np.std(arr, ddof=1)
        if std_r == 0:
            return 0.0

        daily_rf = risk_free_rate / 252
        sharpe = (mean_r - daily_rf) / std_r * math.sqrt(252)
        return sharpe

    def _empty_metrics(self) -> dict:
        return {
            "total_return": 0,
            "annualized_return": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "calmar_ratio": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_trades": 0,
            "avg_holding_days": 0,
            "best_trade_pnl": 0,
            "worst_trade_pnl": 0,
            "consecutive_wins": 0,
            "consecutive_losses": 0,
            "monthly_win_rate": 0,
            "buy_hold_return": 0,
        }

    def _calculate_roc(self, series: pd.Series, period: int) -> pd.Series:
        """計算價格變化率 (Rate of Change)"""
        return ((series - series.shift(period)) / series.shift(period) * 100)

    def _calculate_win_loss_streak(self, trades: List[dict]) -> tuple:
        """計算最長連勝和連敗紀錄"""
        if not trades:
            return 0, 0

        max_win_streak = 0
        max_loss_streak = 0
        current_win_streak = 0
        current_loss_streak = 0

        for trade in trades:
            if trade["pnl"] > 0:
                current_win_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_win_streak)
            elif trade["pnl"] < 0:
                current_loss_streak += 1
                current_win_streak = 0
                max_loss_streak = max(max_loss_streak, current_loss_streak)
            else:
                current_win_streak = 0
                current_loss_streak = 0

        return max_win_streak, max_loss_streak

    def _calculate_monthly_returns(self, equity_curve: List[dict]) -> Dict[str, float]:
        """計算每月報酬率"""
        monthly_returns = {}

        for i, point in enumerate(equity_curve):
            try:
                date_str = point["date"]
                month_key = date_str[:7]  # YYYY-MM 格式

                if month_key not in monthly_returns:
                    monthly_returns[month_key] = {
                        "start_equity": point["equity"],
                        "end_equity": point["equity"],
                    }
                else:
                    monthly_returns[month_key]["end_equity"] = point["equity"]
            except (ValueError, KeyError, IndexError):
                continue

        # 計算月報酬率
        for month_key in monthly_returns:
            start = monthly_returns[month_key]["start_equity"]
            end = monthly_returns[month_key]["end_equity"]
            if start > 0:
                monthly_returns[month_key]["return"] = (end - start) / start * 100
            else:
                monthly_returns[month_key]["return"] = 0

        return monthly_returns

    def _calculate_monthly_win_rate(self, monthly_returns: Dict[str, dict]) -> float:
        """計算月份勝率"""
        if not monthly_returns:
            return 0

        winning_months = sum(1 for m in monthly_returns.values() if m.get("return", 0) > 0)
        return winning_months / len(monthly_returns) * 100 if len(monthly_returns) > 0 else 0

    def _calculate_sortino(self, equity_curve: List[dict], risk_free_rate: float = 0.02) -> float:
        """計算 Sortino Ratio（只考慮下檔波動）"""
        if len(equity_curve) < 2:
            return 0.0

        equities = [p["equity"] for p in equity_curve]
        returns = []

        for i in range(1, len(equities)):
            if equities[i - 1] > 0:
                returns.append((equities[i] - equities[i - 1]) / equities[i - 1])

        if not returns:
            return 0.0

        arr = np.array(returns)
        mean_r = np.mean(arr)

        # 只計算下檔標準差
        downside_returns = arr[arr < 0]
        if len(downside_returns) == 0:
            downside_std = 0
        else:
            downside_std = np.std(downside_returns, ddof=1)

        if downside_std == 0:
            return 0.0

        daily_rf = risk_free_rate / 252
        sortino = (mean_r - daily_rf) / downside_std * math.sqrt(252)
        return sortino

    def _calculate_calmar(self, annualized_return: float, max_drawdown: float) -> float:
        """計算 Calmar Ratio（年化報酬率 / 最大回撤）"""
        if max_drawdown == 0 or max_drawdown < 0:
            return 0.0

        calmar = abs(annualized_return) / max_drawdown
        return calmar

    def compare_strategies(
        self,
        history: List[dict],
        strategies: List[str],
        params_list: List[Dict[str, Any]],
        initial_capital: float = 1_000_000,
    ) -> Dict[str, Any]:
        """
        比較多種策略在同一檔股票上的表現

        Args:
            history: 歷史 OHLCV 資料
            strategies: 策略列表 (e.g., ["ma_crossover", "rsi", "macd"])
            params_list: 對應的參數列表
            initial_capital: 初始資金

        Returns:
            策略比較結果
        """
        if len(strategies) != len(params_list):
            raise ValueError("策略數量與參數數量不符")

        comparison = {
            "total_trades": {},
            "annualized_return": {},
            "max_drawdown": {},
            "sharpe_ratio": {},
            "sortino_ratio": {},
            "calmar_ratio": {},
            "win_rate": {},
            "profit_factor": {},
        }

        results = {}

        for strategy, params in zip(strategies, params_list):
            try:
                result = self.run_backtest(history, strategy, params, initial_capital)
                results[strategy] = result

                # 填充比較表
                metrics = result["metrics"]
                comparison["total_trades"][strategy] = metrics.get("total_trades", 0)
                comparison["annualized_return"][strategy] = metrics.get("annualized_return", 0)
                comparison["max_drawdown"][strategy] = metrics.get("max_drawdown", 0)
                comparison["sharpe_ratio"][strategy] = metrics.get("sharpe_ratio", 0)
                comparison["sortino_ratio"][strategy] = metrics.get("sortino_ratio", 0)
                comparison["calmar_ratio"][strategy] = metrics.get("calmar_ratio", 0)
                win_rate = metrics.get("win_rate", 0)
                comparison["win_rate"][strategy] = win_rate
                comparison["profit_factor"][strategy] = metrics.get("profit_factor", 0)

            except Exception as e:
                logger.error(f"策略 {strategy} 回測失敗: {str(e)}")
                results[strategy] = {"error": str(e)}

        return {
            "comparison_table": comparison,
            "detailed_results": results,
            "best_strategy": self._find_best_strategy(comparison),
        }

    def _find_best_strategy(self, comparison: Dict[str, Dict[str, float]]) -> Dict[str, str]:
        """找出各指標最優的策略"""
        best = {}

        for metric, values in comparison.items():
            if not values:
                continue

            if metric == "max_drawdown":
                # 最大回撤越小越好
                best[metric] = min(values, key=values.get)
            else:
                # 其他指標越大越好
                best[metric] = max(values, key=values.get)

        return best
