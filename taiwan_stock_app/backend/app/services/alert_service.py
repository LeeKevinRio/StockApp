"""
Alert Service
專業級高風險交易分析平台 - 價格告警服務

功能：
- 價格到達告警
- 漲跌幅告警
- 技術信號告警
- 形態突破告警
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum
import json


class AlertType(str, Enum):
    """告警類型"""
    PRICE_ABOVE = "price_above"  # 價格高於
    PRICE_BELOW = "price_below"  # 價格低於
    CHANGE_PERCENT_ABOVE = "change_percent_above"  # 漲幅超過
    CHANGE_PERCENT_BELOW = "change_percent_below"  # 跌幅超過
    VOLUME_ABOVE = "volume_above"  # 成交量超過
    SIGNAL_BUY = "signal_buy"  # 買入信號
    SIGNAL_SELL = "signal_sell"  # 賣出信號
    PATTERN_BREAKOUT = "pattern_breakout"  # 形態突破
    SUPPORT_BREAK = "support_break"  # 跌破支撐
    RESISTANCE_BREAK = "resistance_break"  # 突破阻力


class AlertStatus(str, Enum):
    """告警狀態"""
    ACTIVE = "active"  # 監控中
    TRIGGERED = "triggered"  # 已觸發
    EXPIRED = "expired"  # 已過期
    CANCELLED = "cancelled"  # 已取消


@dataclass
class Alert:
    """告警配置"""
    id: str
    user_id: int
    stock_id: str
    stock_name: str
    alert_type: AlertType
    condition_value: float
    message: str
    status: AlertStatus
    created_at: datetime
    triggered_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


@dataclass
class AlertNotification:
    """告警通知"""
    alert_id: str
    user_id: int
    stock_id: str
    stock_name: str
    alert_type: str
    message: str
    current_value: float
    condition_value: float
    triggered_at: datetime


class AlertService:
    """價格告警服務"""

    def __init__(self):
        # 內存存儲（生產環境應使用 Redis 或數據庫）
        self._alerts: Dict[str, Alert] = {}
        self._user_alerts: Dict[int, List[str]] = {}
        self._notifications: List[AlertNotification] = []

    def create_alert(
        self,
        user_id: int,
        stock_id: str,
        stock_name: str,
        alert_type: AlertType,
        condition_value: float,
        message: Optional[str] = None,
        expires_days: int = 30
    ) -> Alert:
        """
        創建告警

        Args:
            user_id: 用戶 ID
            stock_id: 股票代碼
            stock_name: 股票名稱
            alert_type: 告警類型
            condition_value: 條件值
            message: 自定義消息
            expires_days: 過期天數

        Returns:
            創建的告警
        """
        import uuid
        from datetime import timedelta

        alert_id = str(uuid.uuid4())[:8]

        # 生成默認消息
        if not message:
            message = self._generate_default_message(
                stock_name, stock_id, alert_type, condition_value
            )

        alert = Alert(
            id=alert_id,
            user_id=user_id,
            stock_id=stock_id,
            stock_name=stock_name,
            alert_type=alert_type,
            condition_value=condition_value,
            message=message,
            status=AlertStatus.ACTIVE,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(days=expires_days),
        )

        self._alerts[alert_id] = alert

        if user_id not in self._user_alerts:
            self._user_alerts[user_id] = []
        self._user_alerts[user_id].append(alert_id)

        return alert

    def _generate_default_message(
        self,
        stock_name: str,
        stock_id: str,
        alert_type: AlertType,
        value: float
    ) -> str:
        """生成默認告警消息"""
        messages = {
            AlertType.PRICE_ABOVE: f"{stock_name}({stock_id}) 價格突破 {value:.2f}",
            AlertType.PRICE_BELOW: f"{stock_name}({stock_id}) 價格跌破 {value:.2f}",
            AlertType.CHANGE_PERCENT_ABOVE: f"{stock_name}({stock_id}) 漲幅超過 {value:.1f}%",
            AlertType.CHANGE_PERCENT_BELOW: f"{stock_name}({stock_id}) 跌幅超過 {abs(value):.1f}%",
            AlertType.VOLUME_ABOVE: f"{stock_name}({stock_id}) 成交量超過 {value/10000:.0f} 萬股",
            AlertType.SIGNAL_BUY: f"{stock_name}({stock_id}) 出現買入信號",
            AlertType.SIGNAL_SELL: f"{stock_name}({stock_id}) 出現賣出信號",
            AlertType.PATTERN_BREAKOUT: f"{stock_name}({stock_id}) 形態突破確認",
            AlertType.SUPPORT_BREAK: f"{stock_name}({stock_id}) 跌破支撐位 {value:.2f}",
            AlertType.RESISTANCE_BREAK: f"{stock_name}({stock_id}) 突破阻力位 {value:.2f}",
        }
        return messages.get(alert_type, f"{stock_name} 觸發告警")

    def get_user_alerts(
        self,
        user_id: int,
        status: Optional[AlertStatus] = None
    ) -> List[Alert]:
        """
        取得用戶的所有告警

        Args:
            user_id: 用戶 ID
            status: 篩選狀態

        Returns:
            告警列表
        """
        alert_ids = self._user_alerts.get(user_id, [])
        alerts = [self._alerts[aid] for aid in alert_ids if aid in self._alerts]

        if status:
            alerts = [a for a in alerts if a.status == status]

        return sorted(alerts, key=lambda x: x.created_at, reverse=True)

    def get_stock_alerts(
        self,
        stock_id: str,
        status: Optional[AlertStatus] = None
    ) -> List[Alert]:
        """
        取得某支股票的所有告警

        Args:
            stock_id: 股票代碼
            status: 篩選狀態

        Returns:
            告警列表
        """
        alerts = [a for a in self._alerts.values() if a.stock_id == stock_id]

        if status:
            alerts = [a for a in alerts if a.status == status]

        return alerts

    def cancel_alert(self, alert_id: str, user_id: int) -> bool:
        """
        取消告警

        Args:
            alert_id: 告警 ID
            user_id: 用戶 ID

        Returns:
            是否成功
        """
        alert = self._alerts.get(alert_id)
        if not alert or alert.user_id != user_id:
            return False

        alert.status = AlertStatus.CANCELLED
        return True

    def check_alerts(
        self,
        stock_id: str,
        current_price: float,
        change_percent: float,
        volume: int
    ) -> List[AlertNotification]:
        """
        檢查並觸發告警

        Args:
            stock_id: 股票代碼
            current_price: 當前價格
            change_percent: 漲跌幅
            volume: 成交量

        Returns:
            觸發的告警通知列表
        """
        notifications = []

        for alert in self.get_stock_alerts(stock_id, AlertStatus.ACTIVE):
            triggered = False

            # 檢查是否過期
            if alert.expires_at and datetime.now() > alert.expires_at:
                alert.status = AlertStatus.EXPIRED
                continue

            # 檢查條件
            if alert.alert_type == AlertType.PRICE_ABOVE:
                triggered = current_price >= alert.condition_value
                current_value = current_price
            elif alert.alert_type == AlertType.PRICE_BELOW:
                triggered = current_price <= alert.condition_value
                current_value = current_price
            elif alert.alert_type == AlertType.CHANGE_PERCENT_ABOVE:
                triggered = change_percent >= alert.condition_value
                current_value = change_percent
            elif alert.alert_type == AlertType.CHANGE_PERCENT_BELOW:
                triggered = change_percent <= alert.condition_value
                current_value = change_percent
            elif alert.alert_type == AlertType.VOLUME_ABOVE:
                triggered = volume >= alert.condition_value
                current_value = volume
            else:
                current_value = current_price

            if triggered:
                alert.status = AlertStatus.TRIGGERED
                alert.triggered_at = datetime.now()

                notification = AlertNotification(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    stock_id=alert.stock_id,
                    stock_name=alert.stock_name,
                    alert_type=alert.alert_type.value,
                    message=alert.message,
                    current_value=current_value,
                    condition_value=alert.condition_value,
                    triggered_at=datetime.now(),
                )
                notifications.append(notification)
                self._notifications.append(notification)

        return notifications

    def check_signal_alert(
        self,
        stock_id: str,
        signal: str,  # 'BUY', 'SELL', 'HOLD'
        confidence: float
    ) -> List[AlertNotification]:
        """
        檢查信號告警

        Args:
            stock_id: 股票代碼
            signal: 交易信號
            confidence: 信心度

        Returns:
            觸發的告警通知列表
        """
        notifications = []

        for alert in self.get_stock_alerts(stock_id, AlertStatus.ACTIVE):
            triggered = False

            if alert.alert_type == AlertType.SIGNAL_BUY and signal == 'BUY':
                triggered = confidence >= alert.condition_value
            elif alert.alert_type == AlertType.SIGNAL_SELL and signal == 'SELL':
                triggered = confidence >= alert.condition_value

            if triggered:
                alert.status = AlertStatus.TRIGGERED
                alert.triggered_at = datetime.now()

                notification = AlertNotification(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    stock_id=alert.stock_id,
                    stock_name=alert.stock_name,
                    alert_type=alert.alert_type.value,
                    message=f"{alert.message} (信心度: {confidence:.0f}%)",
                    current_value=confidence,
                    condition_value=alert.condition_value,
                    triggered_at=datetime.now(),
                )
                notifications.append(notification)
                self._notifications.append(notification)

        return notifications

    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[AlertNotification]:
        """
        取得用戶的通知歷史

        Args:
            user_id: 用戶 ID
            limit: 數量限制

        Returns:
            通知列表
        """
        user_notifications = [
            n for n in self._notifications
            if n.user_id == user_id
        ]
        return sorted(
            user_notifications,
            key=lambda x: x.triggered_at,
            reverse=True
        )[:limit]

    def to_dict(self, alert: Alert) -> Dict:
        """將告警轉換為字典"""
        return {
            "id": alert.id,
            "user_id": alert.user_id,
            "stock_id": alert.stock_id,
            "stock_name": alert.stock_name,
            "alert_type": alert.alert_type.value,
            "condition_value": alert.condition_value,
            "message": alert.message,
            "status": alert.status.value,
            "created_at": alert.created_at.isoformat(),
            "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None,
            "expires_at": alert.expires_at.isoformat() if alert.expires_at else None,
        }

    def notification_to_dict(self, notification: AlertNotification) -> Dict:
        """將通知轉換為字典"""
        return {
            "alert_id": notification.alert_id,
            "user_id": notification.user_id,
            "stock_id": notification.stock_id,
            "stock_name": notification.stock_name,
            "alert_type": notification.alert_type,
            "message": notification.message,
            "current_value": notification.current_value,
            "condition_value": notification.condition_value,
            "triggered_at": notification.triggered_at.isoformat(),
        }
