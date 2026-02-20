"""
Alerts router
專業級高風險交易分析平台 - 告警 API
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
import json

logger = logging.getLogger(__name__)

from app.models import User
from app.schemas.alert import (
    AlertCreate,
    AlertResponse,
    AlertListResponse,
    AlertNotificationResponse,
    NotificationListResponse,
    SubscriptionRequest,
    AlertType as SchemaAlertType,
    AlertStatus as SchemaAlertStatus,
)
from app.services.alert_service import AlertService, AlertType, AlertStatus
from app.services.websocket_service import ws_manager
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/alerts", tags=["alerts"])
alert_service = AlertService()


@router.post("", response_model=AlertResponse)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user),
):
    """
    創建價格告警

    告警類型：
    - price_above: 價格高於指定值
    - price_below: 價格低於指定值
    - change_percent_above: 漲幅超過指定百分比
    - change_percent_below: 跌幅超過指定百分比
    - volume_above: 成交量超過指定值
    - signal_buy: 出現買入信號（信心度 >= condition_value）
    - signal_sell: 出現賣出信號（信心度 >= condition_value）
    """
    alert_type = AlertType(alert_data.alert_type.value)

    alert = alert_service.create_alert(
        user_id=current_user.id,
        stock_id=alert_data.stock_id,
        stock_name=alert_data.stock_name,
        alert_type=alert_type,
        condition_value=alert_data.condition_value,
        message=alert_data.message,
        expires_days=alert_data.expires_days,
    )

    return AlertResponse(**alert_service.to_dict(alert))


@router.get("", response_model=AlertListResponse)
async def get_alerts(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """取得用戶的所有告警"""
    alert_status = AlertStatus(status) if status else None
    alerts = alert_service.get_user_alerts(current_user.id, alert_status)

    return AlertListResponse(
        alerts=[AlertResponse(**alert_service.to_dict(a)) for a in alerts],
        total=len(alerts),
    )


@router.delete("/{alert_id}")
async def cancel_alert(
    alert_id: str,
    current_user: User = Depends(get_current_user),
):
    """取消告警"""
    success = alert_service.cancel_alert(alert_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {"message": "Alert cancelled"}


@router.get("/notifications", response_model=NotificationListResponse)
async def get_notifications(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """取得告警通知歷史"""
    notifications = alert_service.get_user_notifications(current_user.id, limit)

    return NotificationListResponse(
        notifications=[
            AlertNotificationResponse(**alert_service.notification_to_dict(n))
            for n in notifications
        ],
        total=len(notifications),
    )


# ==================== WebSocket 端點 ====================

@router.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket 連線端點

    消息格式（客戶端發送）：
    {
        "action": "subscribe" | "unsubscribe",
        "stock_id": "2330",  // 可選
        "broadcast": false   // 可選，是否訂閱廣播
    }

    消息格式（服務端推送）：
    {
        "type": "price_update" | "alert_triggered" | "signal_change",
        "data": {...},
        "timestamp": "2024-01-01T00:00:00"
    }
    """
    # 簡易 token 驗證（生產環境應使用 JWT 驗證）
    # 這裡假設 token 是 user_id
    try:
        user_id = int(token)
    except ValueError:
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 建立連線
    connected = await ws_manager.connect(websocket, user_id)
    if not connected:
        return

    try:
        # 發送連線成功消息
        await ws_manager.send_personal(
            user_id,
            "connected",
            {"message": "WebSocket connected", "user_id": user_id}
        )

        # 處理客戶端消息
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            action = message.get("action")
            stock_id = message.get("stock_id")
            broadcast = message.get("broadcast", False)

            if action == "subscribe":
                if broadcast:
                    await ws_manager.subscribe_broadcast(user_id)
                    await ws_manager.send_personal(
                        user_id,
                        "subscribed",
                        {"broadcast": True}
                    )
                elif stock_id:
                    await ws_manager.subscribe_stock(user_id, stock_id)
                    await ws_manager.send_personal(
                        user_id,
                        "subscribed",
                        {"stock_id": stock_id}
                    )

            elif action == "unsubscribe":
                if stock_id:
                    await ws_manager.unsubscribe_stock(user_id, stock_id)
                    await ws_manager.send_personal(
                        user_id,
                        "unsubscribed",
                        {"stock_id": stock_id}
                    )

            elif action == "ping":
                await ws_manager.send_personal(
                    user_id,
                    "pong",
                    {}
                )

    except WebSocketDisconnect:
        await ws_manager.disconnect(user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await ws_manager.disconnect(user_id)


# ==================== 輔助函數 ====================

async def push_price_update(stock_id: str, price_data: dict):
    """推送價格更新（供其他服務調用）"""
    await ws_manager.push_stock_update(stock_id, price_data)

    # 檢查告警
    notifications = alert_service.check_alerts(
        stock_id=stock_id,
        current_price=price_data.get("current_price", 0),
        change_percent=price_data.get("change_percent", 0),
        volume=price_data.get("volume", 0),
    )

    # 推送告警通知
    for notification in notifications:
        await ws_manager.push_alert_notification(
            notification.user_id,
            alert_service.notification_to_dict(notification)
        )


async def push_signal_update(stock_id: str, signal_data: dict):
    """推送信號更新（供其他服務調用）"""
    await ws_manager.push_signal_change(stock_id, signal_data)

    # 檢查信號告警
    notifications = alert_service.check_signal_alert(
        stock_id=stock_id,
        signal=signal_data.get("signal", "HOLD"),
        confidence=signal_data.get("confidence", 0),
    )

    # 推送告警通知
    for notification in notifications:
        await ws_manager.push_alert_notification(
            notification.user_id,
            alert_service.notification_to_dict(notification)
        )
