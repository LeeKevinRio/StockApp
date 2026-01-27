"""
價格警示服務
"""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.alert import PriceAlert
from app.models.stock import Stock
from app.schemas.alert import PriceAlertCreate, PriceAlertUpdate, AlertTriggerInfo
from app.services.stock_data_service import StockDataService


class AlertService:
    """價格警示服務"""

    def __init__(self):
        self.stock_service = StockDataService()

    def create_alert(self, db: Session, user_id: int, data: PriceAlertCreate) -> PriceAlert:
        """建立價格警示"""
        # 驗證股票存在
        stock = db.query(Stock).filter(Stock.stock_id == data.stock_id).first()
        if not stock:
            raise ValueError(f"股票 {data.stock_id} 不存在")

        # 驗證警示類型和參數
        if data.alert_type in ['ABOVE', 'BELOW']:
            if data.target_price is None:
                raise ValueError("價格警示需要設定目標價格")
        elif data.alert_type in ['PERCENT_UP', 'PERCENT_DOWN']:
            if data.percent_threshold is None:
                raise ValueError("百分比警示需要設定閾值")

        alert = PriceAlert(
            user_id=user_id,
            stock_id=data.stock_id,
            alert_type=data.alert_type,
            target_price=data.target_price,
            percent_threshold=data.percent_threshold,
            notify_push=data.notify_push,
            notify_email=data.notify_email,
            notes=data.notes,
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert

    def get_user_alerts(self, db: Session, user_id: int, active_only: bool = False) -> List[PriceAlert]:
        """取得用戶的價格警示"""
        query = db.query(PriceAlert).filter(PriceAlert.user_id == user_id)
        if active_only:
            query = query.filter(PriceAlert.is_active == True)
        return query.order_by(PriceAlert.created_at.desc()).all()

    def get_alert(self, db: Session, user_id: int, alert_id: int) -> Optional[PriceAlert]:
        """取得單一警示"""
        return db.query(PriceAlert).filter(
            and_(PriceAlert.id == alert_id, PriceAlert.user_id == user_id)
        ).first()

    def update_alert(self, db: Session, user_id: int, alert_id: int, data: PriceAlertUpdate) -> Optional[PriceAlert]:
        """更新價格警示"""
        alert = self.get_alert(db, user_id, alert_id)
        if not alert:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(alert, key, value)

        db.commit()
        db.refresh(alert)
        return alert

    def delete_alert(self, db: Session, user_id: int, alert_id: int) -> bool:
        """刪除價格警示"""
        alert = self.get_alert(db, user_id, alert_id)
        if not alert:
            return False

        db.delete(alert)
        db.commit()
        return True

    def toggle_alert(self, db: Session, user_id: int, alert_id: int) -> Optional[PriceAlert]:
        """切換警示啟用狀態"""
        alert = self.get_alert(db, user_id, alert_id)
        if not alert:
            return None

        alert.is_active = not alert.is_active
        # 如果重新啟用，重置觸發狀態
        if alert.is_active:
            alert.is_triggered = False
            alert.triggered_at = None
            alert.triggered_price = None

        db.commit()
        db.refresh(alert)
        return alert

    def check_alerts(self, db: Session) -> List[AlertTriggerInfo]:
        """檢查所有活躍的警示是否觸發"""
        triggered_alerts = []

        # 獲取所有活躍且未觸發的警示
        active_alerts = db.query(PriceAlert).filter(
            and_(PriceAlert.is_active == True, PriceAlert.is_triggered == False)
        ).all()

        # 按股票分組
        stock_alerts = {}
        for alert in active_alerts:
            if alert.stock_id not in stock_alerts:
                stock_alerts[alert.stock_id] = []
            stock_alerts[alert.stock_id].append(alert)

        # 檢查每個股票的價格
        for stock_id, alerts in stock_alerts.items():
            try:
                price_data = self.stock_service.get_realtime_price(stock_id)
                if not price_data:
                    continue

                current_price = price_data.get('current_price')
                if current_price is None:
                    continue

                current_price = Decimal(str(current_price))

                # 獲取股票名稱
                stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
                stock_name = stock.name if stock else stock_id

                # 檢查每個警示
                for alert in alerts:
                    is_triggered = False
                    message = ""

                    if alert.alert_type == 'ABOVE' and alert.target_price:
                        if current_price >= alert.target_price:
                            is_triggered = True
                            message = f"{stock_name} 價格已突破 {alert.target_price}，目前價格 {current_price}"

                    elif alert.alert_type == 'BELOW' and alert.target_price:
                        if current_price <= alert.target_price:
                            is_triggered = True
                            message = f"{stock_name} 價格已跌破 {alert.target_price}，目前價格 {current_price}"

                    elif alert.alert_type == 'PERCENT_UP' and alert.percent_threshold:
                        change_percent = price_data.get('change_percent', 0)
                        if Decimal(str(change_percent)) >= alert.percent_threshold:
                            is_triggered = True
                            message = f"{stock_name} 漲幅已達 {change_percent:.2f}%，目前價格 {current_price}"

                    elif alert.alert_type == 'PERCENT_DOWN' and alert.percent_threshold:
                        change_percent = price_data.get('change_percent', 0)
                        if Decimal(str(change_percent)) <= -alert.percent_threshold:
                            is_triggered = True
                            message = f"{stock_name} 跌幅已達 {abs(change_percent):.2f}%，目前價格 {current_price}"

                    if is_triggered:
                        # 更新警示狀態
                        alert.is_triggered = True
                        alert.triggered_at = datetime.now()
                        alert.triggered_price = current_price
                        db.commit()

                        triggered_alerts.append(AlertTriggerInfo(
                            alert_id=alert.id,
                            stock_id=stock_id,
                            stock_name=stock_name,
                            alert_type=alert.alert_type,
                            target_price=alert.target_price,
                            current_price=current_price,
                            triggered_at=alert.triggered_at,
                            message=message
                        ))

            except Exception as e:
                print(f"檢查股票 {stock_id} 警示時發生錯誤: {e}")
                continue

        return triggered_alerts

    def get_triggered_alerts(self, db: Session, user_id: int) -> List[PriceAlert]:
        """取得已觸發的警示"""
        return db.query(PriceAlert).filter(
            and_(PriceAlert.user_id == user_id, PriceAlert.is_triggered == True)
        ).order_by(PriceAlert.triggered_at.desc()).all()

    def reset_alert(self, db: Session, user_id: int, alert_id: int) -> Optional[PriceAlert]:
        """重置警示狀態（重新啟用）"""
        alert = self.get_alert(db, user_id, alert_id)
        if not alert:
            return None

        alert.is_triggered = False
        alert.triggered_at = None
        alert.triggered_price = None
        alert.is_active = True

        db.commit()
        db.refresh(alert)
        return alert


# 單例
alert_service = AlertService()
