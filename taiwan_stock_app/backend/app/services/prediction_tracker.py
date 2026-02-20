"""
Prediction Tracker Service - 追蹤 AI 預測準確度
"""
from typing import Dict, List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import logging

from app.models import PredictionRecord, Stock, Watchlist
from app.services import StockDataService
from app.services.trading_calendar import get_next_trading_date

logger = logging.getLogger(__name__)


class PredictionTracker:
    """預測追蹤服務"""

    def __init__(self):
        self.stock_service = StockDataService()

    def save_prediction(
        self,
        db: Session,
        stock_id: str,
        stock_name: str,
        market: str,
        prediction_data: Dict,
        base_close_price: float,
        ai_provider: str = "Unknown"
    ) -> PredictionRecord:
        """
        儲存 AI 預測記錄

        Args:
            db: Database session
            stock_id: 股票代碼
            stock_name: 股票名稱
            market: 市場 (TW/US)
            prediction_data: next_day_prediction 數據
            base_close_price: 預測時的收盤價
            ai_provider: AI 提供者 (Gemini/Groq/Mock)
        """
        today = date.today()
        tomorrow = get_next_trading_date(today, market=market)

        # 檢查是否已存在今日預測
        existing = db.query(PredictionRecord).filter(
            PredictionRecord.stock_id == stock_id,
            PredictionRecord.prediction_date == today
        ).first()

        if existing:
            # 更新現有記錄
            existing.predicted_direction = prediction_data.get("direction")
            existing.predicted_change_percent = prediction_data.get("predicted_change_percent")
            existing.predicted_probability = prediction_data.get("probability")
            existing.predicted_price_low = prediction_data.get("price_range_low")
            existing.predicted_price_high = prediction_data.get("price_range_high")
            existing.prediction_reasoning = prediction_data.get("reasoning")
            existing.base_close_price = base_close_price
            existing.ai_provider = ai_provider
            db.commit()
            return existing

        # 創建新記錄
        record = PredictionRecord(
            stock_id=stock_id,
            stock_name=stock_name,
            market_region=market,
            prediction_date=today,
            target_date=tomorrow,
            predicted_direction=prediction_data.get("direction"),
            predicted_change_percent=prediction_data.get("predicted_change_percent"),
            predicted_probability=prediction_data.get("probability"),
            predicted_price_low=prediction_data.get("price_range_low"),
            predicted_price_high=prediction_data.get("price_range_high"),
            prediction_reasoning=prediction_data.get("reasoning"),
            base_close_price=base_close_price,
            ai_provider=ai_provider
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record

    def update_actual_results(self, db: Session, market: str = None) -> int:
        """
        更新預測的實際結果（收盤後調用）

        Args:
            db: Database session
            market: 市場過濾 (TW/US/None=all)

        Returns:
            更新的記錄數
        """
        today = date.today()

        # 查詢需要更新的預測記錄（目標日期 <= 今天，且還沒有實際結果）
        # 這樣可以補回過去遺漏更新的記錄
        query = db.query(PredictionRecord).filter(
            PredictionRecord.target_date <= today,
            PredictionRecord.actual_close_price.is_(None)
        )

        if market:
            query = query.filter(PredictionRecord.market_region == market)

        records = query.all()
        updated_count = 0

        for record in records:
            try:
                target = record.target_date
                actual_close = 0
                actual_high = 0
                actual_low = 0

                if target == today:
                    # 今天的預測：用即時報價
                    price_data = self.stock_service.get_realtime_price(
                        record.stock_id,
                        market=record.market_region
                    )
                    if price_data:
                        actual_close = float(price_data.get("current_price", 0))
                        actual_high = float(price_data.get("high", 0))
                        actual_low = float(price_data.get("low", 0))
                else:
                    # 過去的預測：用歷史收盤價
                    from app.database import SessionLocal
                    from app.models import StockPrice as StockPriceModel
                    history_price = db.query(StockPriceModel).filter(
                        StockPriceModel.stock_id == record.stock_id,
                        StockPriceModel.date == target
                    ).first()

                    if history_price:
                        actual_close = float(history_price.close or 0)
                        actual_high = float(history_price.high or 0)
                        actual_low = float(history_price.low or 0)
                    else:
                        # 資料庫沒有歷史價，嘗試用 FinMind 取得
                        try:
                            target_str = target.strftime("%Y-%m-%d")
                            df = self.stock_service.finmind.get_stock_price(
                                record.stock_id, target_str, target_str
                            )
                            if len(df) > 0:
                                row = df.iloc[-1]
                                actual_close = float(row.get('close', 0))
                                actual_high = float(row.get('max', row.get('high', 0)))
                                actual_low = float(row.get('min', row.get('low', 0)))
                        except Exception:
                            pass

                    if actual_close <= 0:
                        # 過去的日期仍拿不到資料，嘗試即時報價（可能是今天剛收盤）
                        price_data = self.stock_service.get_realtime_price(
                            record.stock_id,
                            market=record.market_region
                        )
                        if price_data:
                            actual_close = float(price_data.get("current_price", 0))
                            actual_high = float(price_data.get("high", 0))
                            actual_low = float(price_data.get("low", 0))

                base_price = float(record.base_close_price or 0)

                if base_price <= 0 or actual_close <= 0:
                    continue

                # 計算實際漲跌幅
                actual_change = ((actual_close - base_price) / base_price) * 100
                actual_direction = "UP" if actual_change >= 0 else "DOWN"

                # 更新記錄
                record.actual_close_price = actual_close
                record.actual_change_percent = round(actual_change, 2)
                record.actual_direction = actual_direction
                record.actual_high = actual_high
                record.actual_low = actual_low

                # 評估預測
                record.direction_correct = (record.predicted_direction == actual_direction)

                # 檢查收盤價是否在預測區間內
                pred_low = float(record.predicted_price_low or 0)
                pred_high = float(record.predicted_price_high or float('inf'))
                record.within_range = (pred_low <= actual_close <= pred_high)

                # 計算誤差
                pred_change = float(record.predicted_change_percent or 0)
                record.error_percent = round(abs(actual_change - pred_change), 2)

                updated_count += 1

            except Exception as e:
                logger.error(f"Error updating prediction for {record.stock_id}: {e}")
                continue

        db.commit()
        return updated_count

    def get_accuracy_statistics(
        self,
        db: Session,
        days: int = 30,
        market: str = None,
        stock_id: str = None
    ) -> Dict:
        """
        獲取預測準確度統計

        Args:
            db: Database session
            days: 統計天數
            market: 市場過濾
            stock_id: 特定股票

        Returns:
            統計數據
        """
        start_date = date.today() - timedelta(days=days)

        # 基礎查詢
        query = db.query(PredictionRecord).filter(
            PredictionRecord.target_date >= start_date,
            PredictionRecord.actual_close_price.isnot(None)  # 只統計有實際結果的
        )

        if market:
            query = query.filter(PredictionRecord.market_region == market)
        if stock_id:
            query = query.filter(PredictionRecord.stock_id == stock_id)

        records = query.all()

        if not records:
            return {
                "total_predictions": 0,
                "direction_accuracy": 0,
                "within_range_rate": 0,
                "avg_error_percent": 0,
                "records": []
            }

        total = len(records)
        direction_correct = sum(1 for r in records if r.direction_correct)
        within_range = sum(1 for r in records if r.within_range)
        total_error = sum(float(r.error_percent or 0) for r in records)

        # 詳細記錄
        record_details = []
        for r in records[-20:]:  # 最近20筆
            record_details.append({
                "stock_id": r.stock_id,
                "stock_name": r.stock_name,
                "prediction_date": r.prediction_date.isoformat(),
                "target_date": r.target_date.isoformat(),
                "predicted_direction": r.predicted_direction,
                "predicted_change": float(r.predicted_change_percent or 0),
                "actual_direction": r.actual_direction,
                "actual_change": float(r.actual_change_percent or 0),
                "direction_correct": r.direction_correct,
                "error_percent": float(r.error_percent or 0),
                "ai_provider": r.ai_provider
            })

        return {
            "total_predictions": total,
            "direction_accuracy": round((direction_correct / total) * 100, 1),
            "within_range_rate": round((within_range / total) * 100, 1),
            "avg_error_percent": round(total_error / total, 2),
            "direction_correct_count": direction_correct,
            "within_range_count": within_range,
            "period_days": days,
            "records": record_details
        }

    def get_all_stocks_statistics(self, db: Session, days: int = 30) -> Dict:
        """
        獲取所有股票的預測統計（依股票分組）

        Args:
            db: Database session
            days: 統計天數

        Returns:
            各股票的統計數據
        """
        start_date = date.today() - timedelta(days=days)

        # 查詢有實際結果的預測
        records = db.query(PredictionRecord).filter(
            PredictionRecord.target_date >= start_date,
            PredictionRecord.actual_close_price.isnot(None)
        ).order_by(PredictionRecord.target_date.desc()).all()

        # 依股票分組
        stock_data = {}
        for r in records:
            if r.stock_id not in stock_data:
                stock_data[r.stock_id] = {
                    "stock_id": r.stock_id,
                    "stock_name": r.stock_name,
                    "market": r.market_region,
                    "predictions": [],
                    "total": 0,
                    "correct": 0,
                    "total_error": 0,
                }

            stock_data[r.stock_id]["predictions"].append({
                "prediction_date": r.prediction_date.isoformat(),
                "target_date": r.target_date.isoformat(),
                "predicted_direction": r.predicted_direction,
                "predicted_change": float(r.predicted_change_percent or 0),
                "actual_direction": r.actual_direction,
                "actual_change": float(r.actual_change_percent or 0),
                "direction_correct": r.direction_correct,
                "error_percent": float(r.error_percent or 0),
                "ai_provider": r.ai_provider,
            })

            stock_data[r.stock_id]["total"] += 1
            if r.direction_correct:
                stock_data[r.stock_id]["correct"] += 1
            stock_data[r.stock_id]["total_error"] += float(r.error_percent or 0)

        # 計算各股票的準確率
        stocks = []
        for sid, data in stock_data.items():
            total = data["total"]
            correct = data["correct"]
            total_error = data["total_error"]

            stocks.append({
                "stock_id": data["stock_id"],
                "stock_name": data["stock_name"],
                "market": data["market"],
                "total_predictions": total,
                "direction_accuracy": round((correct / total) * 100, 1) if total > 0 else 0,
                "avg_error_percent": round(total_error / total, 2) if total > 0 else 0,
                "correct_count": correct,
                "predictions": data["predictions"][:10],  # 最近 10 筆
            })

        # 依準確率排序
        stocks.sort(key=lambda x: x["direction_accuracy"], reverse=True)

        # 總體統計
        total_all = sum(s["total_predictions"] for s in stocks)
        correct_all = sum(s["correct_count"] for s in stocks)
        error_all = sum(s["avg_error_percent"] * s["total_predictions"] for s in stocks)

        return {
            "period_days": days,
            "total_stocks": len(stocks),
            "total_predictions": total_all,
            "overall_accuracy": round((correct_all / total_all) * 100, 1) if total_all > 0 else 0,
            "overall_avg_error": round(error_all / total_all, 2) if total_all > 0 else 0,
            "stocks": stocks,
        }

    def get_daily_summary(self, db: Session, target_date: date = None) -> Dict:
        """
        獲取特定日期的預測摘要

        Args:
            db: Database session
            target_date: 目標日期（預設昨天）
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        records = db.query(PredictionRecord).filter(
            PredictionRecord.target_date == target_date
        ).all()

        if not records:
            return {
                "date": target_date.isoformat(),
                "total": 0,
                "evaluated": 0,
                "predictions": []
            }

        evaluated = [r for r in records if r.actual_close_price is not None]

        predictions = []
        for r in records:
            pred = {
                "stock_id": r.stock_id,
                "stock_name": r.stock_name,
                "market": r.market_region,
                "predicted_direction": r.predicted_direction,
                "predicted_change": float(r.predicted_change_percent or 0),
                "predicted_probability": float(r.predicted_probability or 0),
                "base_price": float(r.base_close_price or 0),
                "ai_provider": r.ai_provider
            }

            if r.actual_close_price is not None:
                pred.update({
                    "actual_close": float(r.actual_close_price),
                    "actual_change": float(r.actual_change_percent or 0),
                    "actual_direction": r.actual_direction,
                    "direction_correct": r.direction_correct,
                    "error_percent": float(r.error_percent or 0)
                })

            predictions.append(pred)

        # 計算當日統計
        if evaluated:
            direction_correct = sum(1 for r in evaluated if r.direction_correct)
            accuracy = round((direction_correct / len(evaluated)) * 100, 1)
        else:
            accuracy = None

        return {
            "date": target_date.isoformat(),
            "total": len(records),
            "evaluated": len(evaluated),
            "direction_accuracy": accuracy,
            "predictions": predictions
        }

    def get_predictions_made_on(self, db: Session, prediction_date: date = None) -> list:
        """
        取得某天產生的所有預測（不論 target_date）

        Args:
            db: Database session
            prediction_date: 預測產生日期
        """
        if prediction_date is None:
            prediction_date = date.today()

        records = db.query(PredictionRecord).filter(
            PredictionRecord.prediction_date == prediction_date
        ).all()

        results = []
        for r in records:
            pred = {
                "stock_id": r.stock_id,
                "stock_name": r.stock_name,
                "market": r.market_region,
                "prediction_date": r.prediction_date.isoformat(),
                "target_date": r.target_date.isoformat(),
                "predicted_direction": r.predicted_direction,
                "predicted_change": float(r.predicted_change_percent or 0),
                "predicted_probability": float(r.predicted_probability or 0),
                "base_price": float(r.base_close_price or 0),
                "ai_provider": r.ai_provider,
                "status": "verified" if r.actual_close_price is not None else "pending",
            }
            if r.actual_close_price is not None:
                pred.update({
                    "actual_close": float(r.actual_close_price),
                    "actual_change": float(r.actual_change_percent or 0),
                    "actual_direction": r.actual_direction,
                    "direction_correct": r.direction_correct,
                    "error_percent": float(r.error_percent or 0),
                })
            results.append(pred)

        return results
