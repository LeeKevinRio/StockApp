"""
Portfolio Service
專業級高風險交易分析平台 - 投資組合服務

功能：
- 投資組合 CRUD
- 交易記錄
- 持倉計算
- 損益統計
"""

from typing import Dict, List, Optional
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from app.models import Portfolio, Position, Transaction, TransactionType
from app.services import StockDataService

logger = logging.getLogger(__name__)


class PortfolioService:
    """投資組合服務"""

    def __init__(self):
        self.stock_service = StockDataService()

    # ==================== Portfolio CRUD ====================

    def create_portfolio(
        self,
        db: Session,
        user_id: int,
        name: str,
        description: Optional[str] = None,
        initial_capital: float = 0
    ) -> Portfolio:
        """創建投資組合"""
        portfolio = Portfolio(
            user_id=user_id,
            name=name,
            description=description,
            initial_capital=initial_capital,
        )
        db.add(portfolio)
        db.commit()
        db.refresh(portfolio)
        return portfolio

    def get_portfolios(
        self,
        db: Session,
        user_id: int
    ) -> List[Portfolio]:
        """取得用戶的所有投資組合"""
        return db.query(Portfolio).filter(Portfolio.user_id == user_id).all()

    def get_portfolio(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int
    ) -> Optional[Portfolio]:
        """取得單個投資組合"""
        return db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()

    def update_portfolio(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> Optional[Portfolio]:
        """更新投資組合"""
        portfolio = self.get_portfolio(db, portfolio_id, user_id)
        if not portfolio:
            return None

        if name:
            portfolio.name = name
        if description is not None:
            portfolio.description = description

        portfolio.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(portfolio)
        return portfolio

    def delete_portfolio(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int
    ) -> bool:
        """刪除投資組合"""
        portfolio = self.get_portfolio(db, portfolio_id, user_id)
        if not portfolio:
            return False

        db.delete(portfolio)
        db.commit()
        return True

    # ==================== Transactions ====================

    def add_transaction(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int,
        stock_id: str,
        stock_name: str,
        transaction_type: str,
        quantity: int,
        price: float,
        fee: float = 0,
        tax: float = 0,
        notes: Optional[str] = None,
        transaction_date: Optional[datetime] = None
    ) -> Optional[Transaction]:
        """
        新增交易記錄並更新持倉

        Args:
            portfolio_id: 投資組合 ID
            user_id: 用戶 ID
            stock_id: 股票代碼
            stock_name: 股票名稱
            transaction_type: 交易類型 (buy/sell)
            quantity: 數量（股）
            price: 成交價
            fee: 手續費
            tax: 交易稅
            notes: 備註
            transaction_date: 交易日期

        Returns:
            交易記錄
        """
        portfolio = self.get_portfolio(db, portfolio_id, user_id)
        if not portfolio:
            return None

        # 計算總金額
        if transaction_type == "buy":
            total_amount = quantity * price + fee
            tx_type = TransactionType.BUY
        else:
            # 賣出時扣除手續費和交易稅
            total_amount = quantity * price - fee - tax
            tx_type = TransactionType.SELL

        # 創建交易記錄
        transaction = Transaction(
            portfolio_id=portfolio_id,
            stock_id=stock_id,
            stock_name=stock_name,
            transaction_type=tx_type,
            quantity=quantity,
            price=price,
            fee=fee,
            tax=tax,
            total_amount=total_amount,
            notes=notes,
            transaction_date=transaction_date or datetime.utcnow(),
        )
        db.add(transaction)

        # 更新持倉
        self._update_position(
            db, portfolio_id, stock_id, stock_name,
            transaction_type, quantity, price
        )

        db.commit()
        db.refresh(transaction)
        return transaction

    def _update_position(
        self,
        db: Session,
        portfolio_id: int,
        stock_id: str,
        stock_name: str,
        transaction_type: str,
        quantity: int,
        price: float
    ):
        """更新持倉"""
        position = db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.stock_id == stock_id
        ).first()

        if transaction_type == "buy":
            if position:
                # 更新平均成本
                total_cost = position.avg_cost * position.quantity + price * quantity
                total_quantity = position.quantity + quantity
                position.avg_cost = total_cost / total_quantity if total_quantity > 0 else 0
                position.quantity = total_quantity
            else:
                # 新建持倉
                position = Position(
                    portfolio_id=portfolio_id,
                    stock_id=stock_id,
                    stock_name=stock_name,
                    quantity=quantity,
                    avg_cost=price,
                )
                db.add(position)
        else:  # sell
            if position:
                position.quantity -= quantity
                if position.quantity <= 0:
                    # 清倉時刪除持倉記錄
                    db.delete(position)

    def get_transactions(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int,
        limit: int = 50
    ) -> List[Transaction]:
        """取得交易記錄"""
        portfolio = self.get_portfolio(db, portfolio_id, user_id)
        if not portfolio:
            return []

        return db.query(Transaction).filter(
            Transaction.portfolio_id == portfolio_id
        ).order_by(Transaction.transaction_date.desc()).limit(limit).all()

    # ==================== Positions ====================

    def get_positions(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int
    ) -> List[Position]:
        """取得持倉列表"""
        portfolio = self.get_portfolio(db, portfolio_id, user_id)
        if not portfolio:
            return []

        return db.query(Position).filter(
            Position.portfolio_id == portfolio_id,
            Position.quantity > 0
        ).all()

    def update_positions_price(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int
    ) -> List[Position]:
        """
        更新所有持倉的當前價格和未實現損益

        Returns:
            更新後的持倉列表
        """
        positions = self.get_positions(db, portfolio_id, user_id)

        for position in positions:
            try:
                price_data = self.stock_service.get_realtime_price(position.stock_id)
                if price_data:
                    current_price = float(price_data.get('current_price', 0))
                    position.current_price = current_price

                    # 計算未實現損益
                    market_value = current_price * position.quantity
                    cost_value = position.avg_cost * position.quantity
                    position.unrealized_pnl = market_value - cost_value
                    position.unrealized_pnl_percent = (
                        (position.unrealized_pnl / cost_value * 100)
                        if cost_value > 0 else 0
                    )
                    position.last_updated = datetime.utcnow()
            except Exception as e:
                logger.error("更新持倉價格失敗 %s: %s", position.stock_id, e)

        db.commit()
        return positions

    # ==================== Statistics ====================

    def get_portfolio_summary(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int
    ) -> Dict:
        """
        取得投資組合摘要

        Returns:
            摘要數據
        """
        portfolio = self.get_portfolio(db, portfolio_id, user_id)
        if not portfolio:
            return {}

        # 更新價格
        positions = self.update_positions_price(db, portfolio_id, user_id)

        total_value = 0
        total_cost = 0
        winning = 0
        losing = 0
        best_performer = None
        worst_performer = None
        best_return = float('-inf')
        worst_return = float('inf')

        for position in positions:
            market_value = position.current_price * position.quantity
            cost_value = position.avg_cost * position.quantity

            total_value += market_value
            total_cost += cost_value

            if position.unrealized_pnl > 0:
                winning += 1
            elif position.unrealized_pnl < 0:
                losing += 1

            if position.unrealized_pnl_percent > best_return:
                best_return = position.unrealized_pnl_percent
                best_performer = f"{position.stock_name} (+{position.unrealized_pnl_percent:.1f}%)"

            if position.unrealized_pnl_percent < worst_return:
                worst_return = position.unrealized_pnl_percent
                worst_performer = f"{position.stock_name} ({position.unrealized_pnl_percent:.1f}%)"

        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        # 現金餘額計算（簡化：初始資金 - 總成本）
        cash_balance = portfolio.initial_capital - total_cost

        return {
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_percent": round(total_pnl_percent, 2),
            "cash_balance": round(cash_balance, 2),
            "positions_count": len(positions),
            "winning_positions": winning,
            "losing_positions": losing,
            "best_performer": best_performer,
            "worst_performer": worst_performer,
        }

    def get_position_allocation(
        self,
        db: Session,
        portfolio_id: int,
        user_id: int
    ) -> List[Dict]:
        """
        取得持倉配置

        Returns:
            持倉配置列表
        """
        positions = self.get_positions(db, portfolio_id, user_id)

        total_value = sum(
            p.current_price * p.quantity for p in positions
        )

        allocations = []
        for position in positions:
            market_value = position.current_price * position.quantity
            weight = (market_value / total_value * 100) if total_value > 0 else 0

            allocations.append({
                "stock_id": position.stock_id,
                "stock_name": position.stock_name,
                "market_value": round(market_value, 2),
                "weight": round(weight, 2),
            })

        # 按權重排序
        allocations.sort(key=lambda x: x['weight'], reverse=True)
        return allocations
