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
from app.services.trading_calendar import get_next_trading_date, get_previous_trading_date

logger = logging.getLogger(__name__)


class PredictionTracker:
    """預測追蹤服務"""

    def __init__(self):
        self.stock_service = StockDataService()

    @staticmethod
    def _dedup_records(records: list) -> list:
        """
        對 (stock_id, target_date) 去重，只保留最新 prediction_date 的記錄。
        避免歷史重複預測膨脹誤差統計。
        """
        best = {}
        for r in records:
            key = (r.stock_id, r.target_date)
            if key not in best or r.prediction_date > best[key].prediction_date:
                best[key] = r
        return list(best.values())

    def _get_prev_trading_day_close(
        self, db: Session, stock_id: str, target_date: date
    ) -> Optional[float]:
        """
        取得 target_date 前一個交易日的收盤價，
        用於修正因長假導致的陳舊 base_close_price。
        """
        prev_td = get_previous_trading_date(target_date, market="TW")
        # 1. 先查 DB
        from app.models import StockPrice as StockPriceModel
        hist = db.query(StockPriceModel).filter(
            StockPriceModel.stock_id == stock_id,
            StockPriceModel.date == prev_td
        ).first()
        if hist and float(hist.close or 0) > 0:
            return float(hist.close)

        # 2. 查 FinMind（API 有時會多回傳後續日期，需精確篩選）
        try:
            prev_str = prev_td.strftime("%Y-%m-%d")
            df = self.stock_service.finmind.get_stock_price(
                stock_id, prev_str, prev_str
            )
            if len(df) > 0:
                # 精確過濾到目標日期
                exact = df[df["date"].astype(str) == prev_str]
                row = exact.iloc[0] if len(exact) > 0 else df.iloc[0]
                return float(row.get("close", 0))
        except Exception:
            pass

        # 3. 查同 stock 已驗證的 PredictionRecord（prev_td 作為 target_date）
        prev_pred = db.query(PredictionRecord).filter(
            PredictionRecord.stock_id == stock_id,
            PredictionRecord.target_date == prev_td,
            PredictionRecord.actual_close_price.isnot(None)
        ).first()
        if prev_pred and float(prev_pred.actual_close_price or 0) > 0:
            return float(prev_pred.actual_close_price)

        return None

    @staticmethod
    def _detect_market(stock_id: str, market_hint: str = "TW") -> str:
        """
        根據股票代碼自動偵測市場，防止 market 標記錯誤。
        台股代碼為純數字（含 ETF 如 00631L），美股為英文字母開頭。
        """
        # 純英文字母 → 美股
        if stock_id.isalpha():
            return "US"
        # 純數字或數字開頭（如 2330, 00631L）→ 台股
        if stock_id[0].isdigit():
            return "TW"
        # fallback 使用提示值
        return market_hint

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
        # 防呆：自動修正 market 標記錯誤
        detected = self._detect_market(stock_id, market)
        if detected != market:
            logger.warning("Market 自動修正: %s %s -> %s", stock_id, market, detected)
            market = detected

        today = date.today()
        tomorrow = get_next_trading_date(today, market=market)

        # 以 stock_id + target_date 去重：同一目標日只保留最新預測
        existing = db.query(PredictionRecord).filter(
            PredictionRecord.stock_id == stock_id,
            PredictionRecord.target_date == tomorrow
        ).first()

        if existing:
            # 更新現有記錄（含 prediction_date 更新為今天）
            existing.prediction_date = today
            existing.predicted_direction = prediction_data.get("direction")
            existing.predicted_change_percent = prediction_data.get("predicted_change_percent")
            existing.predicted_probability = prediction_data.get("probability")
            existing.predicted_price_low = prediction_data.get("price_range_low")
            existing.predicted_price_high = prediction_data.get("price_range_high")
            existing.prediction_reasoning = prediction_data.get("reasoning")
            existing.base_close_price = base_close_price
            existing.ai_provider = ai_provider
            # 清除舊的 actual 結果，讓它重新計算
            existing.actual_close_price = None
            existing.actual_change_percent = None
            existing.actual_direction = None
            existing.direction_correct = None
            existing.within_range = None
            existing.error_percent = None
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

        # 查詢需要更新的預測記錄：
        # 1. 目標日期 <= 今天，且還沒有實際結果（補回過去遺漏的）
        # 2. 目標日期 == 今天，即使已有結果也重新更新（盤中價格持續變動）
        from sqlalchemy import or_
        query = db.query(PredictionRecord).filter(
            PredictionRecord.target_date <= today,
            or_(
                PredictionRecord.actual_close_price.is_(None),
                PredictionRecord.target_date == today,  # 今天的預測隨時更新
            )
        )

        if market:
            query = query.filter(PredictionRecord.market_region == market)

        records = query.all()
        logger.info(f"update_actual_results: found {len(records)} records to check (market={market})")
        updated_count = 0

        for record in records:
            try:
                # 防呆：修正 market_region 標記錯誤
                detected = self._detect_market(record.stock_id, record.market_region)
                if detected != record.market_region:
                    logger.warning("修正 %s market: %s -> %s", record.stock_id, record.market_region, detected)
                    record.market_region = detected

                target = record.target_date
                actual_close = 0
                actual_high = 0
                actual_low = 0

                logger.info(f"Processing {record.stock_id}: target={target}, today={today}, base={record.base_close_price}, market={record.market_region}")
                if target == today:
                    # 今天的預測：用即時報價
                    price_data = self.stock_service.get_realtime_price(
                        record.stock_id,
                        market=record.market_region
                    )
                    logger.info(f"  {record.stock_id} realtime: price_data={price_data is not None}, close={price_data.get('current_price') if price_data else 'N/A'}")
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

                # base_price=0 修復：從即時報價的漲跌幅反推前一日收盤
                if base_price <= 0 and actual_close > 0 and price_data:
                    cp = float(price_data.get("change_percent", 0))
                    if cp != 0:
                        base_price = round(actual_close / (1 + cp / 100), 2)
                    else:
                        base_price = actual_close
                    record.base_close_price = base_price
                    logger.info(f"Auto-fix base_price for {record.stock_id}: {base_price}")

                if base_price <= 0 or actual_close <= 0:
                    logger.warning(
                        f"Skip {record.stock_id} (target={target}): base={base_price}, actual_close={actual_close}"
                    )
                    continue

                # === 台股 base_price 修正 ===
                # 台股每日漲跌幅限制 ±10%，如果 base_price 過於陳舊
                # （例如長假前的價格），會導致計算出超過 10% 的漲跌幅。
                # 修正方式：用 target_date 前一個交易日的收盤價取代。
                if record.market_region == "TW":
                    raw_change = ((actual_close - base_price) / base_price) * 100
                    if abs(raw_change) > 10.5:  # 超過漲跌停（含小數誤差）
                        corrected_base = self._get_prev_trading_day_close(
                            db, record.stock_id, target
                        )
                        if corrected_base and corrected_base > 0:
                            logger.info(
                                "修正 %s base_price: %.2f -> %.2f (原算 %.1f%%)",
                                record.stock_id, base_price, corrected_base, raw_change
                            )
                            base_price = corrected_base
                            record.base_close_price = corrected_base

                # 計算實際漲跌幅
                actual_change = ((actual_close - base_price) / base_price) * 100

                # 台股漲跌幅上限安全夾（±10%），避免資料異常
                if record.market_region == "TW" and abs(actual_change) > 10.5:
                    actual_change = max(min(actual_change, 10.0), -10.0)

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

        records = self._dedup_records(query.all())

        if not records:
            return {
                "total_predictions": 0,
                "direction_accuracy": 0,
                "within_range_rate": 0,
                "avg_error_percent": 0,
                "records": [],
                "provider_breakdown": {}
            }

        total = len(records)
        direction_correct = sum(1 for r in records if r.direction_correct)
        within_range = sum(1 for r in records if r.within_range)
        total_error = sum(float(r.error_percent or 0) for r in records)

        # 2c: provider_breakdown — 各 AI 提供者的統計
        provider_stats = {}
        for r in records:
            prov = r.ai_provider or "Unknown"
            if prov not in provider_stats:
                provider_stats[prov] = {"total": 0, "correct": 0, "total_error": 0}
            provider_stats[prov]["total"] += 1
            if r.direction_correct:
                provider_stats[prov]["correct"] += 1
            provider_stats[prov]["total_error"] += float(r.error_percent or 0)

        provider_breakdown = {}
        for prov, s in provider_stats.items():
            provider_breakdown[prov] = {
                "total": s["total"],
                "direction_accuracy": round((s["correct"] / s["total"]) * 100, 1) if s["total"] > 0 else 0,
                "avg_error": round(s["total_error"] / s["total"], 2) if s["total"] > 0 else 0,
            }

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
            "provider_breakdown": provider_breakdown,
            "records": record_details
        }

    def get_all_stocks_statistics(self, db: Session, days: int = 30, market: str = None) -> Dict:
        """
        獲取所有股票的預測統計（依股票分組）

        Args:
            db: Database session
            days: 統計天數
            market: 市場過濾 (TW/US/None=all)

        Returns:
            各股票的統計數據
        """
        start_date = date.today() - timedelta(days=days)

        # 查詢有實際結果的預測，並去重
        query = db.query(PredictionRecord).filter(
            PredictionRecord.target_date >= start_date,
            PredictionRecord.actual_close_price.isnot(None)
        )
        if market:
            query = query.filter(PredictionRecord.market_region == market)
        records = self._dedup_records(
            query.order_by(PredictionRecord.target_date.desc()).all()
        )

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

    def get_daily_summary(self, db: Session, target_date: date = None, market: str = None) -> Dict:
        """
        獲取特定日期的預測摘要

        Args:
            db: Database session
            target_date: 目標日期（預設昨天）
            market: 市場過濾 (TW/US/None=all)
        """
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        query = db.query(PredictionRecord).filter(
            PredictionRecord.target_date == target_date
        )
        if market:
            query = query.filter(PredictionRecord.market_region == market)
        records = self._dedup_records(query.all())

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

    def get_predictions_made_on(self, db: Session, prediction_date: date = None, market: str = None) -> list:
        """
        取得某天產生的所有預測（不論 target_date）

        Args:
            db: Database session
            prediction_date: 預測產生日期
            market: 市場過濾 (TW/US/None=all)
        """
        if prediction_date is None:
            prediction_date = date.today()

        query = db.query(PredictionRecord).filter(
            PredictionRecord.prediction_date == prediction_date
        )
        if market:
            query = query.filter(PredictionRecord.market_region == market)
        records = query.all()

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
