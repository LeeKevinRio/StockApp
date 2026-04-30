"""
模擬交易服務
"""
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.trading import VirtualAccount, VirtualPosition, VirtualOrder
from app.models import Stock
from app.services import StockDataService


class TradingService:
    """模擬交易服務"""

    def __init__(self):
        self.stock_service = StockDataService()

    def get_or_create_account(self, db: Session, user_id: int) -> VirtualAccount:
        """獲取或創建虛擬帳戶"""
        account = db.query(VirtualAccount).filter(
            VirtualAccount.user_id == user_id
        ).first()

        if not account:
            account = VirtualAccount(
                user_id=user_id,
                initial_balance=Decimal('1000000'),
                cash_balance=Decimal('1000000'),
                total_value=Decimal('1000000'),
            )
            db.add(account)
            db.commit()
            db.refresh(account)

        return account

    def get_account_summary(self, db: Session, user_id: int) -> Dict:
        """獲取帳戶摘要"""
        account = self.get_or_create_account(db, user_id)

        # 更新持倉市值
        self._update_positions_value(db, account)

        # 獲取持倉
        positions = db.query(VirtualPosition).filter(
            VirtualPosition.account_id == account.id,
            VirtualPosition.quantity > 0
        ).all()

        # 獲取近期訂單
        recent_orders = db.query(VirtualOrder).filter(
            VirtualOrder.account_id == account.id
        ).order_by(VirtualOrder.created_at.desc()).limit(20).all()

        return {
            'account': self._account_to_dict(account),
            'positions': [self._position_to_dict(db, p) for p in positions],
            'recent_orders': [self._order_to_dict(db, o) for o in recent_orders],
        }

    def place_order(
        self,
        db: Session,
        user_id: int,
        stock_id: str,
        order_type: str,
        quantity: int,
        price: float
    ) -> Dict:
        """下單"""
        account = self.get_or_create_account(db, user_id)

        # 驗證訂單
        validation = self._validate_order(db, account, stock_id, order_type, quantity, price)
        if not validation['valid']:
            return {
                'success': False,
                'message': validation['message'],
                'order': None
            }

        # 創建訂單
        order = VirtualOrder(
            account_id=account.id,
            stock_id=stock_id,
            order_type=order_type,
            quantity=quantity,
            price=Decimal(str(price)),
            status='PENDING'
        )
        db.add(order)
        db.commit()

        # 模擬即時成交
        result = self._execute_order(db, order, account)

        return result

    def _validate_order(
        self,
        db: Session,
        account: VirtualAccount,
        stock_id: str,
        order_type: str,
        quantity: int,
        price: float
    ) -> Dict:
        """驗證訂單"""
        if quantity <= 0:
            return {'valid': False, 'message': '數量必須大於 0'}

        if price <= 0:
            return {'valid': False, 'message': '價格必須大於 0'}

        # 檢查股票是否存在
        stock = db.query(Stock).filter(Stock.stock_id == stock_id).first()
        if not stock:
            return {'valid': False, 'message': f'股票 {stock_id} 不存在'}

        if order_type == 'BUY':
            # 檢查資金是否足夠
            total_cost = Decimal(str(price)) * quantity
            if account.cash_balance < total_cost:
                return {'valid': False, 'message': f'資金不足，需要 {total_cost}，餘額 {account.cash_balance}'}
        elif order_type == 'SELL':
            # 檢查持倉是否足夠
            position = db.query(VirtualPosition).filter(
                VirtualPosition.account_id == account.id,
                VirtualPosition.stock_id == stock_id
            ).first()
            if not position or position.quantity < quantity:
                current_qty = position.quantity if position else 0
                return {'valid': False, 'message': f'持倉不足，持有 {current_qty} 股，欲賣出 {quantity} 股'}
        else:
            return {'valid': False, 'message': '無效的訂單類型'}

        return {'valid': True, 'message': 'OK'}

    def _execute_order(self, db: Session, order: VirtualOrder, account: VirtualAccount) -> Dict:
        """執行訂單（模擬即時成交）"""
        try:
            order.status = 'FILLED'
            order.filled_quantity = order.quantity
            order.filled_price = order.price
            order.filled_at = datetime.now()

            if order.order_type == 'BUY':
                self._execute_buy(db, order, account)
            else:
                self._execute_sell(db, order, account)

            db.commit()

            return {
                'success': True,
                'message': f'{order.order_type} 訂單已成交',
                'order': self._order_to_dict(db, order)
            }
        except Exception as e:
            db.rollback()
            order.status = 'FAILED'
            db.commit()
            return {
                'success': False,
                'message': f'訂單執行失敗: {str(e)}',
                'order': None
            }

    def _execute_buy(self, db: Session, order: VirtualOrder, account: VirtualAccount):
        """執行買入"""
        total_cost = order.price * order.quantity

        # 扣除現金
        account.cash_balance -= total_cost

        # 更新或創建持倉
        position = db.query(VirtualPosition).filter(
            VirtualPosition.account_id == account.id,
            VirtualPosition.stock_id == order.stock_id
        ).first()

        if position:
            # 更新平均成本
            old_value = position.avg_cost * position.quantity
            new_value = order.price * order.quantity
            position.quantity += order.quantity
            position.avg_cost = (old_value + new_value) / position.quantity
        else:
            position = VirtualPosition(
                account_id=account.id,
                stock_id=order.stock_id,
                quantity=order.quantity,
                avg_cost=order.price,
            )
            db.add(position)

        # 更新帳戶總值
        self._update_account_value(db, account)

    def _execute_sell(self, db: Session, order: VirtualOrder, account: VirtualAccount):
        """執行賣出"""
        total_proceeds = order.price * order.quantity

        # 增加現金
        account.cash_balance += total_proceeds

        # 更新持倉
        position = db.query(VirtualPosition).filter(
            VirtualPosition.account_id == account.id,
            VirtualPosition.stock_id == order.stock_id
        ).first()

        if position:
            position.quantity -= order.quantity
            if position.quantity <= 0:
                db.delete(position)

        # 更新帳戶總值
        self._update_account_value(db, account)

    def _update_positions_value(self, db: Session, account: VirtualAccount):
        """更新所有持倉的市值"""
        positions = db.query(VirtualPosition).filter(
            VirtualPosition.account_id == account.id
        ).all()

        for position in positions:
            # 獲取當前價格（推測市場以正確路由 yfinance vs TWSE）
            sid = position.stock_id or ""
            _market = "US" if sid.isalpha() else "TW"
            price_data = self.stock_service.get_realtime_price(sid, market=_market)
            if price_data and 'current_price' in price_data:
                current_price = Decimal(str(price_data['current_price']))
                position.current_price = current_price
                position.market_value = current_price * position.quantity

                # 計算未實現損益
                cost_value = position.avg_cost * position.quantity
                position.unrealized_pnl = position.market_value - cost_value
                if cost_value > 0:
                    position.unrealized_pnl_percent = float(position.unrealized_pnl / cost_value * 100)

        self._update_account_value(db, account)
        db.commit()

    def _update_account_value(self, db: Session, account: VirtualAccount):
        """更新帳戶總值"""
        positions = db.query(VirtualPosition).filter(
            VirtualPosition.account_id == account.id
        ).all()

        total_market_value = sum(
            p.market_value or (p.avg_cost * p.quantity)
            for p in positions
        )
        account.total_value = account.cash_balance + total_market_value
        account.total_profit_loss = account.total_value - account.initial_balance
        if account.initial_balance > 0:
            account.total_profit_loss_percent = float(
                account.total_profit_loss / account.initial_balance * 100
            )

    def cancel_order(self, db: Session, user_id: int, order_id: int) -> Dict:
        """取消訂單"""
        account = self.get_or_create_account(db, user_id)

        order = db.query(VirtualOrder).filter(
            VirtualOrder.id == order_id,
            VirtualOrder.account_id == account.id
        ).first()

        if not order:
            return {'success': False, 'message': '訂單不存在'}

        if order.status != 'PENDING':
            return {'success': False, 'message': '只能取消待處理的訂單'}

        order.status = 'CANCELLED'
        db.commit()

        return {'success': True, 'message': '訂單已取消'}

    def reset_account(self, db: Session, user_id: int) -> Dict:
        """重置帳戶"""
        account = self.get_or_create_account(db, user_id)

        # 刪除所有持倉和訂單
        db.query(VirtualPosition).filter(
            VirtualPosition.account_id == account.id
        ).delete()
        db.query(VirtualOrder).filter(
            VirtualOrder.account_id == account.id
        ).delete()

        # 重置帳戶資金
        account.cash_balance = account.initial_balance
        account.total_value = account.initial_balance
        account.total_profit_loss = Decimal('0')
        account.total_profit_loss_percent = Decimal('0')

        db.commit()

        return {'success': True, 'message': '帳戶已重置'}

    def _account_to_dict(self, account: VirtualAccount) -> Dict:
        return {
            'id': account.id,
            'user_id': account.user_id,
            'initial_balance': float(account.initial_balance),
            'cash_balance': float(account.cash_balance),
            'total_value': float(account.total_value),
            'total_profit_loss': float(account.total_profit_loss),
            'total_profit_loss_percent': float(account.total_profit_loss_percent),
            'created_at': account.created_at.isoformat() if account.created_at else None,
        }

    def _position_to_dict(self, db: Session, position: VirtualPosition) -> Dict:
        stock = db.query(Stock).filter(Stock.stock_id == position.stock_id).first()
        return {
            'id': position.id,
            'stock_id': position.stock_id,
            'stock_name': stock.name if stock else None,
            'quantity': position.quantity,
            'avg_cost': float(position.avg_cost) if position.avg_cost else 0,
            'current_price': float(position.current_price) if position.current_price else None,
            'market_value': float(position.market_value) if position.market_value else None,
            'unrealized_pnl': float(position.unrealized_pnl) if position.unrealized_pnl else 0,
            'unrealized_pnl_percent': float(position.unrealized_pnl_percent) if position.unrealized_pnl_percent else 0,
        }

    def _order_to_dict(self, db: Session, order: VirtualOrder) -> Dict:
        stock = db.query(Stock).filter(Stock.stock_id == order.stock_id).first()
        return {
            'id': order.id,
            'stock_id': order.stock_id,
            'stock_name': stock.name if stock else None,
            'order_type': order.order_type,
            'quantity': order.quantity,
            'price': float(order.price),
            'filled_quantity': order.filled_quantity,
            'filled_price': float(order.filled_price) if order.filled_price else None,
            'status': order.status,
            'created_at': order.created_at.isoformat() if order.created_at else None,
            'filled_at': order.filled_at.isoformat() if order.filled_at else None,
        }


# 單例
trading_service = TradingService()
