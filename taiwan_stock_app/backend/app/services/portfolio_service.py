"""
Portfolio Service
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.models.portfolio import Portfolio, PortfolioHolding, PortfolioSnapshot
from app.models.stock import Stock
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate,
    PortfolioHoldingCreate, PortfolioHoldingUpdate,
    PortfolioSummary, PortfolioDetailResponse, PortfolioHoldingResponse,
    PortfolioPerformance, PortfolioSnapshotResponse,
    PortfolioAllocation, PortfolioAllocationResponse
)
from app.data_fetchers.twse_fetcher import get_stock_realtime_price


class PortfolioService:
    """投資組合服務"""

    def __init__(self, db: Session):
        self.db = db

    def create_portfolio(self, user_id: int, data: PortfolioCreate) -> Portfolio:
        """建立投資組合"""
        # 如果設為預設，先取消其他預設
        if data.is_default:
            self.db.query(Portfolio).filter(
                Portfolio.user_id == user_id,
                Portfolio.is_default == True
            ).update({"is_default": False})

        portfolio = Portfolio(
            user_id=user_id,
            name=data.name,
            description=data.description,
            is_default=data.is_default
        )
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def get_user_portfolios(self, user_id: int) -> List[PortfolioSummary]:
        """取得用戶所有組合摘要"""
        portfolios = self.db.query(Portfolio).filter(
            Portfolio.user_id == user_id
        ).all()

        summaries = []
        for portfolio in portfolios:
            summary = self._calculate_portfolio_summary(portfolio)
            summaries.append(summary)

        return summaries

    def get_portfolio_detail(self, portfolio_id: int, user_id: int) -> Optional[PortfolioDetailResponse]:
        """取得組合詳情"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()

        if not portfolio:
            return None

        holdings_response = []
        total_cost = Decimal(0)
        total_value = Decimal(0)

        for holding in portfolio.holdings:
            holding_data = self._enrich_holding(holding)
            holdings_response.append(holding_data)
            total_cost += Decimal(holding.quantity) * holding.avg_cost
            if holding_data.market_value:
                total_value += holding_data.market_value

        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else Decimal(0)

        return PortfolioDetailResponse(
            id=portfolio.id,
            user_id=portfolio.user_id,
            name=portfolio.name,
            description=portfolio.description,
            is_default=portfolio.is_default,
            created_at=portfolio.created_at,
            updated_at=portfolio.updated_at,
            holdings=holdings_response,
            total_cost=total_cost,
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent
        )

    def update_portfolio(self, portfolio_id: int, user_id: int, data: PortfolioUpdate) -> Optional[Portfolio]:
        """更新組合"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()

        if not portfolio:
            return None

        if data.name:
            portfolio.name = data.name
        if data.description is not None:
            portfolio.description = data.description

        self.db.commit()
        self.db.refresh(portfolio)
        return portfolio

    def delete_portfolio(self, portfolio_id: int, user_id: int) -> bool:
        """刪除組合"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()

        if not portfolio:
            return False

        self.db.delete(portfolio)
        self.db.commit()
        return True

    def add_holding(self, portfolio_id: int, user_id: int, data: PortfolioHoldingCreate) -> Optional[PortfolioHolding]:
        """新增持股"""
        # 確認組合存在且屬於用戶
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()

        if not portfolio:
            return None

        # 檢查是否已有相同股票
        existing = self.db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio_id,
            PortfolioHolding.stock_id == data.stock_id
        ).first()

        if existing:
            # 合併持股 (計算加權平均成本)
            total_quantity = existing.quantity + data.quantity
            total_cost = (existing.quantity * existing.avg_cost) + (data.quantity * data.avg_cost)
            existing.avg_cost = total_cost / total_quantity
            existing.quantity = total_quantity
            self.db.commit()
            self.db.refresh(existing)
            return existing

        holding = PortfolioHolding(
            portfolio_id=portfolio_id,
            stock_id=data.stock_id,
            quantity=data.quantity,
            avg_cost=data.avg_cost,
            buy_date=data.buy_date,
            notes=data.notes
        )
        self.db.add(holding)
        self.db.commit()
        self.db.refresh(holding)
        return holding

    def update_holding(self, holding_id: int, user_id: int, data: PortfolioHoldingUpdate) -> Optional[PortfolioHolding]:
        """更新持股"""
        holding = self.db.query(PortfolioHolding).join(Portfolio).filter(
            PortfolioHolding.id == holding_id,
            Portfolio.user_id == user_id
        ).first()

        if not holding:
            return None

        if data.quantity is not None:
            holding.quantity = data.quantity
        if data.avg_cost is not None:
            holding.avg_cost = data.avg_cost
        if data.notes is not None:
            holding.notes = data.notes

        self.db.commit()
        self.db.refresh(holding)
        return holding

    def delete_holding(self, holding_id: int, user_id: int) -> bool:
        """刪除持股"""
        holding = self.db.query(PortfolioHolding).join(Portfolio).filter(
            PortfolioHolding.id == holding_id,
            Portfolio.user_id == user_id
        ).first()

        if not holding:
            return False

        self.db.delete(holding)
        self.db.commit()
        return True

    def get_portfolio_performance(
        self,
        portfolio_id: int,
        user_id: int,
        days: int = 30
    ) -> Optional[PortfolioPerformance]:
        """取得組合績效"""
        portfolio = self.db.query(Portfolio).filter(
            Portfolio.id == portfolio_id,
            Portfolio.user_id == user_id
        ).first()

        if not portfolio:
            return None

        end_date = date.today()
        start_date = end_date - timedelta(days=days)

        snapshots = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id,
            PortfolioSnapshot.date >= start_date,
            PortfolioSnapshot.date <= end_date
        ).order_by(PortfolioSnapshot.date).all()

        if not snapshots:
            # 沒有快照，返回當前數據
            detail = self.get_portfolio_detail(portfolio_id, user_id)
            if not detail:
                return None

            return PortfolioPerformance(
                portfolio_id=portfolio_id,
                portfolio_name=portfolio.name,
                period_days=days,
                start_value=detail.total_cost,
                end_value=detail.total_value,
                absolute_return=detail.total_pnl,
                percent_return=detail.total_pnl_percent,
                snapshots=[]
            )

        start_value = snapshots[0].total_value
        end_value = snapshots[-1].total_value
        absolute_return = end_value - start_value
        percent_return = (absolute_return / start_value * 100) if start_value > 0 else Decimal(0)

        return PortfolioPerformance(
            portfolio_id=portfolio_id,
            portfolio_name=portfolio.name,
            period_days=days,
            start_value=start_value,
            end_value=end_value,
            absolute_return=absolute_return,
            percent_return=percent_return,
            snapshots=[
                PortfolioSnapshotResponse(
                    date=s.date,
                    total_value=s.total_value,
                    total_cost=s.total_cost,
                    daily_return=s.daily_return,
                    total_return=s.total_return
                ) for s in snapshots
            ]
        )

    def get_portfolio_allocation(self, portfolio_id: int, user_id: int) -> Optional[PortfolioAllocationResponse]:
        """取得持股配置"""
        detail = self.get_portfolio_detail(portfolio_id, user_id)
        if not detail:
            return None

        allocations = []
        for holding in detail.holdings:
            if holding.market_value and holding.market_value > 0:
                weight = (holding.market_value / detail.total_value * 100) if detail.total_value > 0 else Decimal(0)
                allocations.append(PortfolioAllocation(
                    stock_id=holding.stock_id,
                    stock_name=holding.stock_name or holding.stock_id,
                    market_value=holding.market_value,
                    weight=weight
                ))

        # 按權重排序
        allocations.sort(key=lambda x: x.weight, reverse=True)

        return PortfolioAllocationResponse(
            portfolio_id=portfolio_id,
            portfolio_name=detail.name,
            total_value=detail.total_value,
            allocations=allocations
        )

    def take_snapshot(self, portfolio_id: int, user_id: int) -> Optional[PortfolioSnapshot]:
        """建立組合快照"""
        detail = self.get_portfolio_detail(portfolio_id, user_id)
        if not detail:
            return None

        today = date.today()

        # 檢查今天是否已有快照
        existing = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id,
            PortfolioSnapshot.date == today
        ).first()

        if existing:
            # 更新現有快照
            existing.total_value = detail.total_value
            existing.total_cost = detail.total_cost
            existing.total_return = detail.total_pnl_percent
            self.db.commit()
            self.db.refresh(existing)
            return existing

        # 計算日報酬
        yesterday = today - timedelta(days=1)
        yesterday_snapshot = self.db.query(PortfolioSnapshot).filter(
            PortfolioSnapshot.portfolio_id == portfolio_id,
            PortfolioSnapshot.date == yesterday
        ).first()

        daily_return = None
        if yesterday_snapshot and yesterday_snapshot.total_value > 0:
            daily_return = ((detail.total_value - yesterday_snapshot.total_value)
                           / yesterday_snapshot.total_value * 100)

        snapshot = PortfolioSnapshot(
            portfolio_id=portfolio_id,
            date=today,
            total_value=detail.total_value,
            total_cost=detail.total_cost,
            daily_return=daily_return,
            total_return=detail.total_pnl_percent
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def _calculate_portfolio_summary(self, portfolio: Portfolio) -> PortfolioSummary:
        """計算組合摘要"""
        total_cost = Decimal(0)
        total_value = Decimal(0)

        for holding in portfolio.holdings:
            cost = Decimal(holding.quantity) * holding.avg_cost
            total_cost += cost

            # 取得即時價格
            try:
                price_data = get_stock_realtime_price(holding.stock_id)
                if price_data and price_data.get("current_price"):
                    current_price = Decimal(str(price_data["current_price"]))
                    total_value += Decimal(holding.quantity) * current_price
                else:
                    total_value += cost  # 無法取得價格時使用成本
            except Exception:
                total_value += cost

        total_pnl = total_value - total_cost
        total_pnl_percent = (total_pnl / total_cost * 100) if total_cost > 0 else Decimal(0)

        return PortfolioSummary(
            id=portfolio.id,
            name=portfolio.name,
            total_cost=total_cost,
            total_value=total_value,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            holdings_count=len(portfolio.holdings)
        )

    def _enrich_holding(self, holding: PortfolioHolding) -> PortfolioHoldingResponse:
        """填充持股資訊"""
        # 取得股票名稱
        stock = self.db.query(Stock).filter(Stock.stock_id == holding.stock_id).first()
        stock_name = stock.name if stock else None

        # 取得即時價格
        current_price = None
        market_value = None
        unrealized_pnl = None
        unrealized_pnl_percent = None

        try:
            price_data = get_stock_realtime_price(holding.stock_id)
            if price_data and price_data.get("current_price"):
                current_price = Decimal(str(price_data["current_price"]))
                market_value = Decimal(holding.quantity) * current_price
                cost = Decimal(holding.quantity) * holding.avg_cost
                unrealized_pnl = market_value - cost
                unrealized_pnl_percent = (unrealized_pnl / cost * 100) if cost > 0 else Decimal(0)
        except Exception:
            pass

        return PortfolioHoldingResponse(
            id=holding.id,
            portfolio_id=holding.portfolio_id,
            stock_id=holding.stock_id,
            quantity=holding.quantity,
            avg_cost=holding.avg_cost,
            buy_date=holding.buy_date,
            notes=holding.notes,
            stock_name=stock_name,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_percent=unrealized_pnl_percent,
            created_at=holding.created_at
        )
