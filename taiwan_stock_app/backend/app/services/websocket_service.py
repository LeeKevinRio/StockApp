"""
WebSocket Service
專業級高風險交易分析平台 - 實時推送服務

功能：
- 即時報價推送
- 告警通知推送
- 信號變化通知
- 連線管理
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
from fastapi import WebSocket
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConnectionInfo:
    """連線資訊"""
    websocket: WebSocket
    user_id: int
    subscribed_stocks: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)


class WebSocketManager:
    """WebSocket 連線管理器"""

    def __init__(self):
        # 用戶連線: user_id -> ConnectionInfo
        self._connections: Dict[int, ConnectionInfo] = {}
        # 股票訂閱: stock_id -> Set[user_id]
        self._stock_subscribers: Dict[str, Set[int]] = {}
        # 廣播連線（接收所有推送）
        self._broadcast_connections: Set[int] = set()

    async def connect(self, websocket: WebSocket, user_id: int) -> bool:
        """
        建立 WebSocket 連線

        Args:
            websocket: WebSocket 實例
            user_id: 用戶 ID

        Returns:
            是否成功連線
        """
        try:
            await websocket.accept()
            self._connections[user_id] = ConnectionInfo(
                websocket=websocket,
                user_id=user_id,
            )
            logger.info("WebSocket 連線建立: user_id=%d", user_id)
            return True
        except Exception as e:
            logger.error("WebSocket 連線失敗: %s", e)
            return False

    async def disconnect(self, user_id: int):
        """
        斷開 WebSocket 連線

        Args:
            user_id: 用戶 ID
        """
        if user_id in self._connections:
            conn = self._connections[user_id]

            # 移除訂閱
            for stock_id in conn.subscribed_stocks:
                if stock_id in self._stock_subscribers:
                    self._stock_subscribers[stock_id].discard(user_id)

            # 移除廣播
            self._broadcast_connections.discard(user_id)

            # 移除連線
            del self._connections[user_id]
            logger.info("WebSocket 連線斷開: user_id=%d", user_id)

    async def subscribe_stock(self, user_id: int, stock_id: str) -> bool:
        """
        訂閱股票即時報價

        Args:
            user_id: 用戶 ID
            stock_id: 股票代碼

        Returns:
            是否成功訂閱
        """
        if user_id not in self._connections:
            return False

        self._connections[user_id].subscribed_stocks.add(stock_id)

        if stock_id not in self._stock_subscribers:
            self._stock_subscribers[stock_id] = set()
        self._stock_subscribers[stock_id].add(user_id)

        logger.info("用戶 %d 訂閱 %s", user_id, stock_id)
        return True

    async def unsubscribe_stock(self, user_id: int, stock_id: str) -> bool:
        """
        取消訂閱股票

        Args:
            user_id: 用戶 ID
            stock_id: 股票代碼

        Returns:
            是否成功取消
        """
        if user_id not in self._connections:
            return False

        self._connections[user_id].subscribed_stocks.discard(stock_id)

        if stock_id in self._stock_subscribers:
            self._stock_subscribers[stock_id].discard(user_id)

        return True

    async def subscribe_broadcast(self, user_id: int) -> bool:
        """
        訂閱廣播（接收所有推送）

        Args:
            user_id: 用戶 ID

        Returns:
            是否成功訂閱
        """
        if user_id not in self._connections:
            return False

        self._broadcast_connections.add(user_id)
        return True

    async def send_personal(
        self,
        user_id: int,
        message_type: str,
        data: Dict
    ) -> bool:
        """
        發送個人訊息

        Args:
            user_id: 用戶 ID
            message_type: 訊息類型
            data: 數據

        Returns:
            是否成功發送
        """
        if user_id not in self._connections:
            return False

        try:
            message = {
                "type": message_type,
                "data": data,
                "timestamp": datetime.now().isoformat(),
            }
            await self._connections[user_id].websocket.send_json(message)
            return True
        except Exception as e:
            logger.error("發送訊息失敗: %s", e)
            await self.disconnect(user_id)
            return False

    async def push_stock_update(
        self,
        stock_id: str,
        price_data: Dict
    ):
        """
        推送股票即時報價更新

        Args:
            stock_id: 股票代碼
            price_data: 報價數據
        """
        subscribers = self._stock_subscribers.get(stock_id, set())

        for user_id in list(subscribers):
            await self.send_personal(
                user_id,
                "price_update",
                {
                    "stock_id": stock_id,
                    **price_data,
                }
            )

    async def push_alert_notification(
        self,
        user_id: int,
        notification: Dict
    ):
        """
        推送告警通知

        Args:
            user_id: 用戶 ID
            notification: 通知數據
        """
        await self.send_personal(
            user_id,
            "alert_triggered",
            notification
        )

    async def push_signal_change(
        self,
        stock_id: str,
        signal_data: Dict
    ):
        """
        推送交易信號變化

        Args:
            stock_id: 股票代碼
            signal_data: 信號數據
        """
        subscribers = self._stock_subscribers.get(stock_id, set())

        for user_id in list(subscribers):
            await self.send_personal(
                user_id,
                "signal_change",
                {
                    "stock_id": stock_id,
                    **signal_data,
                }
            )

    async def broadcast(
        self,
        message_type: str,
        data: Dict
    ):
        """
        廣播訊息給所有廣播訂閱者

        Args:
            message_type: 訊息類型
            data: 數據
        """
        for user_id in list(self._broadcast_connections):
            await self.send_personal(user_id, message_type, data)

    async def broadcast_all(
        self,
        message_type: str,
        data: Dict
    ):
        """
        廣播訊息給所有連線用戶

        Args:
            message_type: 訊息類型
            data: 數據
        """
        for user_id in list(self._connections.keys()):
            await self.send_personal(user_id, message_type, data)

    def get_connection_stats(self) -> Dict:
        """取得連線統計"""
        return {
            "total_connections": len(self._connections),
            "broadcast_subscribers": len(self._broadcast_connections),
            "stock_subscriptions": {
                stock_id: len(users)
                for stock_id, users in self._stock_subscribers.items()
            },
        }

    def get_user_subscriptions(self, user_id: int) -> List[str]:
        """取得用戶的訂閱列表"""
        if user_id not in self._connections:
            return []
        return list(self._connections[user_id].subscribed_stocks)


# 全局 WebSocket 管理器實例
ws_manager = WebSocketManager()
