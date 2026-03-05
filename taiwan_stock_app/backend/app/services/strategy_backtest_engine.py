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
            equity_curve.append({
                "date": date_str,
                "equity": round(equity, 2),
                "drawdown": 0.0,  # 之後計算
            })

        # 計算回撤
        if equity_curve:
            peak = equity_curve[0]["equity"]
            for point in equity_curve:
                if point["equity"] > peak:
                    peak = point["equity"]
                dd = (peak - point["equity"]) / peak * 100 if peak > 0 else 0
                point["drawdown"] = round(dd, 2)

        return trades, equity_curve

    # ---- 績效計算 ----

    def _calculate_metrics(
        self,
        trades: List[dict],
        equity_curve: List[dict],
        initial_capital: float,
    ) -> dict:
        """計算績效指標"""
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

        # 最大回撤
        max_drawdown = max((p["drawdown"] for p in equity_curve), default=0)

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
        else:
            win_rate = 0
            avg_holding = 0
            profit_factor = 0

        # Sharpe Ratio（簡化版：用日報酬率計算）
        sharpe = self._calculate_sharpe(equity_curve)

        return {
            "total_return": round(total_return, 2),
            "annualized_return": round(annualized, 2),
            "max_drawdown": round(max_drawdown, 2),
            "sharpe_ratio": round(sharpe, 2),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2) if profit_factor != float("inf") else 999.99,
            "total_trades": total_trades,
            "avg_holding_days": round(avg_holding, 1),
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
            "win_rate": 0,
            "profit_factor": 0,
            "total_trades": 0,
            "avg_holding_days": 0,
        }
