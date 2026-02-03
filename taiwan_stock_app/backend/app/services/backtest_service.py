"""
Backtest Service
專業級高風險交易分析平台 - 回測和績效統計服務

功能：
- AI 建議準確率統計
- 按建議類型分析
- 按產業分析
- 按信心度分析
- 模擬交易回測
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from enum import Enum
import statistics
import json


class TradeResult(str, Enum):
    """交易結果"""
    WIN = "win"  # 獲利
    LOSS = "loss"  # 虧損
    BREAK_EVEN = "break_even"  # 平手
    PENDING = "pending"  # 未平倉


@dataclass
class SuggestionRecord:
    """AI 建議記錄"""
    id: str
    stock_id: str
    stock_name: str
    suggestion: str  # BUY, SELL, HOLD
    confidence: float  # 0-100
    entry_price: float
    target_price: float
    stop_loss: float
    report_date: date
    industry: Optional[str] = None
    actual_result: Optional[TradeResult] = None
    exit_price: Optional[float] = None
    exit_date: Optional[date] = None
    return_percent: Optional[float] = None
    holding_days: Optional[int] = None


@dataclass
class PerformanceStats:
    """績效統計"""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    break_even_trades: int = 0
    pending_trades: int = 0
    win_rate: float = 0.0
    avg_return: float = 0.0
    max_return: float = 0.0
    min_return: float = 0.0
    avg_holding_days: float = 0.0
    profit_factor: float = 0.0  # 總獲利 / 總虧損
    sharpe_ratio: float = 0.0  # 夏普比率（簡化版）


class BacktestService:
    """回測和績效統計服務"""

    def __init__(self):
        # 內存存儲（生產環境應使用數據庫）
        self._records: Dict[str, SuggestionRecord] = {}
        self._stock_records: Dict[str, List[str]] = {}  # stock_id -> [record_ids]

    def record_suggestion(
        self,
        stock_id: str,
        stock_name: str,
        suggestion: str,
        confidence: float,
        entry_price: float,
        target_price: float,
        stop_loss: float,
        industry: Optional[str] = None
    ) -> SuggestionRecord:
        """
        記錄 AI 建議

        Args:
            stock_id: 股票代碼
            stock_name: 股票名稱
            suggestion: 建議類型 (BUY/SELL/HOLD)
            confidence: 信心度
            entry_price: 建議進場價
            target_price: 目標價
            stop_loss: 停損價
            industry: 產業分類

        Returns:
            建議記錄
        """
        import uuid
        record_id = str(uuid.uuid4())[:8]

        record = SuggestionRecord(
            id=record_id,
            stock_id=stock_id,
            stock_name=stock_name,
            suggestion=suggestion,
            confidence=confidence,
            entry_price=entry_price,
            target_price=target_price,
            stop_loss=stop_loss,
            report_date=date.today(),
            industry=industry,
        )

        self._records[record_id] = record

        if stock_id not in self._stock_records:
            self._stock_records[stock_id] = []
        self._stock_records[stock_id].append(record_id)

        return record

    def update_result(
        self,
        record_id: str,
        exit_price: float,
        exit_date: Optional[date] = None
    ) -> Optional[SuggestionRecord]:
        """
        更新交易結果

        Args:
            record_id: 記錄 ID
            exit_price: 出場價
            exit_date: 出場日期

        Returns:
            更新後的記錄
        """
        record = self._records.get(record_id)
        if not record:
            return None

        record.exit_price = exit_price
        record.exit_date = exit_date or date.today()

        # 計算報酬率
        if record.suggestion == "BUY":
            record.return_percent = (exit_price - record.entry_price) / record.entry_price * 100
        elif record.suggestion == "SELL":
            record.return_percent = (record.entry_price - exit_price) / record.entry_price * 100
        else:
            record.return_percent = 0

        # 判斷結果
        if record.return_percent > 0.5:
            record.actual_result = TradeResult.WIN
        elif record.return_percent < -0.5:
            record.actual_result = TradeResult.LOSS
        else:
            record.actual_result = TradeResult.BREAK_EVEN

        # 計算持有天數
        record.holding_days = (record.exit_date - record.report_date).days

        return record

    def auto_evaluate_suggestions(
        self,
        stock_id: str,
        current_price: float,
        days_threshold: int = 10
    ) -> List[SuggestionRecord]:
        """
        自動評估建議結果

        檢查是否達到目標價或停損價，或持有超過指定天數

        Args:
            stock_id: 股票代碼
            current_price: 當前價格
            days_threshold: 自動平倉天數

        Returns:
            更新後的記錄列表
        """
        updated = []
        record_ids = self._stock_records.get(stock_id, [])

        for record_id in record_ids:
            record = self._records.get(record_id)
            if not record or record.actual_result is not None:
                continue

            days_held = (date.today() - record.report_date).days

            # 檢查是否達到目標價或停損價
            if record.suggestion == "BUY":
                if current_price >= record.target_price:
                    self.update_result(record_id, current_price)
                    updated.append(record)
                elif current_price <= record.stop_loss:
                    self.update_result(record_id, current_price)
                    updated.append(record)
                elif days_held >= days_threshold:
                    self.update_result(record_id, current_price)
                    updated.append(record)

            elif record.suggestion == "SELL":
                if current_price <= record.target_price:
                    self.update_result(record_id, current_price)
                    updated.append(record)
                elif current_price >= record.stop_loss:
                    self.update_result(record_id, current_price)
                    updated.append(record)
                elif days_held >= days_threshold:
                    self.update_result(record_id, current_price)
                    updated.append(record)

        return updated

    def calculate_performance(
        self,
        records: Optional[List[SuggestionRecord]] = None
    ) -> PerformanceStats:
        """
        計算績效統計

        Args:
            records: 要計算的記錄列表，若為 None 則計算所有記錄

        Returns:
            績效統計
        """
        if records is None:
            records = list(self._records.values())

        closed_records = [r for r in records if r.actual_result is not None]

        if not closed_records:
            return PerformanceStats()

        stats = PerformanceStats()
        stats.total_trades = len(closed_records)
        stats.winning_trades = len([r for r in closed_records if r.actual_result == TradeResult.WIN])
        stats.losing_trades = len([r for r in closed_records if r.actual_result == TradeResult.LOSS])
        stats.break_even_trades = len([r for r in closed_records if r.actual_result == TradeResult.BREAK_EVEN])
        stats.pending_trades = len([r for r in records if r.actual_result is None])

        # 勝率
        if stats.total_trades > 0:
            stats.win_rate = stats.winning_trades / stats.total_trades * 100

        # 報酬率統計
        returns = [r.return_percent for r in closed_records if r.return_percent is not None]
        if returns:
            stats.avg_return = statistics.mean(returns)
            stats.max_return = max(returns)
            stats.min_return = min(returns)

        # 持有天數統計
        holding_days = [r.holding_days for r in closed_records if r.holding_days is not None]
        if holding_days:
            stats.avg_holding_days = statistics.mean(holding_days)

        # 獲利因子
        total_profit = sum(r.return_percent for r in closed_records if r.return_percent and r.return_percent > 0)
        total_loss = abs(sum(r.return_percent for r in closed_records if r.return_percent and r.return_percent < 0))
        if total_loss > 0:
            stats.profit_factor = total_profit / total_loss

        # 簡化版夏普比率
        if len(returns) > 1:
            std_dev = statistics.stdev(returns)
            if std_dev > 0:
                stats.sharpe_ratio = stats.avg_return / std_dev

        return stats

    def get_performance_by_suggestion(self) -> Dict[str, PerformanceStats]:
        """按建議類型分析績效"""
        result = {}
        for suggestion_type in ["BUY", "SELL", "HOLD"]:
            records = [r for r in self._records.values() if r.suggestion == suggestion_type]
            result[suggestion_type] = self.calculate_performance(records)
        return result

    def get_performance_by_confidence(self) -> Dict[str, PerformanceStats]:
        """按信心度區間分析績效"""
        ranges = [
            ("低信心度 (<50)", 0, 50),
            ("中信心度 (50-70)", 50, 70),
            ("高信心度 (>=70)", 70, 101),
        ]

        result = {}
        for name, low, high in ranges:
            records = [r for r in self._records.values() if low <= r.confidence < high]
            result[name] = self.calculate_performance(records)
        return result

    def get_performance_by_industry(self) -> Dict[str, PerformanceStats]:
        """按產業分析績效"""
        industries = set(r.industry for r in self._records.values() if r.industry)
        result = {}
        for industry in industries:
            records = [r for r in self._records.values() if r.industry == industry]
            result[industry] = self.calculate_performance(records)
        return result

    def get_recent_records(
        self,
        limit: int = 50,
        suggestion_filter: Optional[str] = None
    ) -> List[SuggestionRecord]:
        """
        取得最近的建議記錄

        Args:
            limit: 數量限制
            suggestion_filter: 建議類型篩選

        Returns:
            建議記錄列表
        """
        records = list(self._records.values())

        if suggestion_filter:
            records = [r for r in records if r.suggestion == suggestion_filter]

        records.sort(key=lambda x: x.report_date, reverse=True)
        return records[:limit]

    def get_accuracy_trend(self, days: int = 30) -> List[Dict]:
        """
        取得準確率趨勢

        Args:
            days: 天數

        Returns:
            每日準確率統計列表
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        trend = []
        current_date = start_date

        while current_date <= end_date:
            day_records = [
                r for r in self._records.values()
                if r.report_date == current_date and r.actual_result is not None
            ]

            if day_records:
                wins = len([r for r in day_records if r.actual_result == TradeResult.WIN])
                total = len(day_records)
                accuracy = wins / total * 100

                trend.append({
                    "date": current_date.isoformat(),
                    "total": total,
                    "wins": wins,
                    "accuracy": round(accuracy, 1),
                })

            current_date += timedelta(days=1)

        return trend

    def generate_performance_report(self) -> Dict:
        """
        生成完整績效報告

        Returns:
            績效報告字典
        """
        overall = self.calculate_performance()
        by_suggestion = self.get_performance_by_suggestion()
        by_confidence = self.get_performance_by_confidence()
        by_industry = self.get_performance_by_industry()

        return {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_trades": overall.total_trades,
                "win_rate": round(overall.win_rate, 1),
                "avg_return": round(overall.avg_return, 2),
                "profit_factor": round(overall.profit_factor, 2),
                "sharpe_ratio": round(overall.sharpe_ratio, 2),
            },
            "overall": self._stats_to_dict(overall),
            "by_suggestion": {k: self._stats_to_dict(v) for k, v in by_suggestion.items()},
            "by_confidence": {k: self._stats_to_dict(v) for k, v in by_confidence.items()},
            "by_industry": {k: self._stats_to_dict(v) for k, v in by_industry.items()},
            "accuracy_trend": self.get_accuracy_trend(30),
        }

    def _stats_to_dict(self, stats: PerformanceStats) -> Dict:
        """將績效統計轉換為字典"""
        return {
            "total_trades": stats.total_trades,
            "winning_trades": stats.winning_trades,
            "losing_trades": stats.losing_trades,
            "break_even_trades": stats.break_even_trades,
            "pending_trades": stats.pending_trades,
            "win_rate": round(stats.win_rate, 1),
            "avg_return": round(stats.avg_return, 2),
            "max_return": round(stats.max_return, 2),
            "min_return": round(stats.min_return, 2),
            "avg_holding_days": round(stats.avg_holding_days, 1),
            "profit_factor": round(stats.profit_factor, 2),
            "sharpe_ratio": round(stats.sharpe_ratio, 2),
        }

    def record_to_dict(self, record: SuggestionRecord) -> Dict:
        """將建議記錄轉換為字典"""
        return {
            "id": record.id,
            "stock_id": record.stock_id,
            "stock_name": record.stock_name,
            "suggestion": record.suggestion,
            "confidence": record.confidence,
            "entry_price": record.entry_price,
            "target_price": record.target_price,
            "stop_loss": record.stop_loss,
            "report_date": record.report_date.isoformat(),
            "industry": record.industry,
            "actual_result": record.actual_result.value if record.actual_result else None,
            "exit_price": record.exit_price,
            "exit_date": record.exit_date.isoformat() if record.exit_date else None,
            "return_percent": round(record.return_percent, 2) if record.return_percent else None,
            "holding_days": record.holding_days,
        }
