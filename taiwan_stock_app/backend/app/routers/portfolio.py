"""
Portfolio router
專業級高風險交易分析平台 - 投資組合 API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User
from app.schemas.portfolio import (
    PortfolioCreate,
    PortfolioUpdate,
    PortfolioResponse,
    PortfolioListResponse,
    PositionResponse,
    PositionListResponse,
    TransactionCreate,
    TransactionResponse,
    TransactionListResponse,
    PortfolioSummary,
    PositionAllocation,
)
from app.services.portfolio_service import PortfolioService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/portfolios", tags=["portfolios"])
portfolio_service = PortfolioService()


# ==================== Portfolio CRUD ====================

@router.post("", response_model=PortfolioResponse)
def create_portfolio(
    request: PortfolioCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """創建投資組合"""
    portfolio = portfolio_service.create_portfolio(
        db=db,
        user_id=current_user.id,
        name=request.name,
        description=request.description,
        initial_capital=request.initial_capital,
    )

    # 計算摘要
    summary = portfolio_service.get_portfolio_summary(db, portfolio.id, current_user.id)

    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        description=portfolio.description,
        initial_capital=portfolio.initial_capital,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        total_value=summary.get("total_value", 0),
        total_cost=summary.get("total_cost", 0),
        total_pnl=summary.get("total_pnl", 0),
        total_pnl_percent=summary.get("total_pnl_percent", 0),
        positions_count=summary.get("positions_count", 0),
    )


@router.get("", response_model=PortfolioListResponse)
def get_portfolios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得用戶的所有投資組合"""
    portfolios = portfolio_service.get_portfolios(db, current_user.id)

    response_list = []
    for p in portfolios:
        summary = portfolio_service.get_portfolio_summary(db, p.id, current_user.id)
        response_list.append(PortfolioResponse(
            id=p.id,
            user_id=p.user_id,
            name=p.name,
            description=p.description,
            initial_capital=p.initial_capital,
            created_at=p.created_at,
            updated_at=p.updated_at,
            total_value=summary.get("total_value", 0),
            total_cost=summary.get("total_cost", 0),
            total_pnl=summary.get("total_pnl", 0),
            total_pnl_percent=summary.get("total_pnl_percent", 0),
            positions_count=summary.get("positions_count", 0),
        ))

    return PortfolioListResponse(portfolios=response_list, total=len(response_list))


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得單個投資組合"""
    portfolio = portfolio_service.get_portfolio(db, portfolio_id, current_user.id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    summary = portfolio_service.get_portfolio_summary(db, portfolio_id, current_user.id)

    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        description=portfolio.description,
        initial_capital=portfolio.initial_capital,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        total_value=summary.get("total_value", 0),
        total_cost=summary.get("total_cost", 0),
        total_pnl=summary.get("total_pnl", 0),
        total_pnl_percent=summary.get("total_pnl_percent", 0),
        positions_count=summary.get("positions_count", 0),
    )


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int,
    request: PortfolioUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新投資組合"""
    portfolio = portfolio_service.update_portfolio(
        db=db,
        portfolio_id=portfolio_id,
        user_id=current_user.id,
        name=request.name,
        description=request.description,
    )
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    summary = portfolio_service.get_portfolio_summary(db, portfolio_id, current_user.id)

    return PortfolioResponse(
        id=portfolio.id,
        user_id=portfolio.user_id,
        name=portfolio.name,
        description=portfolio.description,
        initial_capital=portfolio.initial_capital,
        created_at=portfolio.created_at,
        updated_at=portfolio.updated_at,
        total_value=summary.get("total_value", 0),
        total_cost=summary.get("total_cost", 0),
        total_pnl=summary.get("total_pnl", 0),
        total_pnl_percent=summary.get("total_pnl_percent", 0),
        positions_count=summary.get("positions_count", 0),
    )


@router.delete("/{portfolio_id}")
def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刪除投資組合"""
    success = portfolio_service.delete_portfolio(db, portfolio_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return {"message": "Portfolio deleted"}


# ==================== Transactions ====================

@router.post("/{portfolio_id}/transactions", response_model=TransactionResponse)
def add_transaction(
    portfolio_id: int,
    request: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    新增交易記錄

    交易類型：
    - buy: 買入
    - sell: 賣出

    自動更新持倉和計算損益
    """
    transaction = portfolio_service.add_transaction(
        db=db,
        portfolio_id=portfolio_id,
        user_id=current_user.id,
        stock_id=request.stock_id,
        stock_name=request.stock_name,
        transaction_type=request.transaction_type.value,
        quantity=request.quantity,
        price=request.price,
        fee=request.fee,
        tax=request.tax,
        notes=request.notes,
        transaction_date=request.transaction_date,
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return TransactionResponse(
        id=transaction.id,
        portfolio_id=transaction.portfolio_id,
        stock_id=transaction.stock_id,
        stock_name=transaction.stock_name,
        transaction_type=transaction.transaction_type.value,
        quantity=transaction.quantity,
        price=transaction.price,
        fee=transaction.fee,
        tax=transaction.tax,
        total_amount=transaction.total_amount,
        notes=transaction.notes,
        transaction_date=transaction.transaction_date,
        created_at=transaction.created_at,
    )


@router.get("/{portfolio_id}/transactions", response_model=TransactionListResponse)
def get_transactions(
    portfolio_id: int,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得交易記錄"""
    transactions = portfolio_service.get_transactions(
        db, portfolio_id, current_user.id, limit
    )

    return TransactionListResponse(
        transactions=[
            TransactionResponse(
                id=t.id,
                portfolio_id=t.portfolio_id,
                stock_id=t.stock_id,
                stock_name=t.stock_name,
                transaction_type=t.transaction_type.value,
                quantity=t.quantity,
                price=t.price,
                fee=t.fee,
                tax=t.tax,
                total_amount=t.total_amount,
                notes=t.notes,
                transaction_date=t.transaction_date,
                created_at=t.created_at,
            )
            for t in transactions
        ],
        total=len(transactions),
    )


# ==================== Positions ====================

@router.get("/{portfolio_id}/positions", response_model=PositionListResponse)
def get_positions(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得持倉列表（自動更新價格）"""
    positions = portfolio_service.update_positions_price(
        db, portfolio_id, current_user.id
    )

    return PositionListResponse(
        positions=[
            PositionResponse(
                id=p.id,
                portfolio_id=p.portfolio_id,
                stock_id=p.stock_id,
                stock_name=p.stock_name,
                quantity=p.quantity,
                avg_cost=p.avg_cost,
                current_price=p.current_price,
                market_value=p.current_price * p.quantity,
                unrealized_pnl=p.unrealized_pnl,
                unrealized_pnl_percent=p.unrealized_pnl_percent,
                last_updated=p.last_updated,
            )
            for p in positions
        ],
        total=len(positions),
    )


# ==================== Statistics ====================

@router.get("/{portfolio_id}/summary", response_model=PortfolioSummary)
def get_portfolio_summary(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得投資組合摘要"""
    summary = portfolio_service.get_portfolio_summary(db, portfolio_id, current_user.id)
    if not summary:
        raise HTTPException(status_code=404, detail="Portfolio not found")

    return PortfolioSummary(**summary)


@router.get("/{portfolio_id}/allocation", response_model=List[PositionAllocation])
def get_position_allocation(
    portfolio_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得持倉配置"""
    allocations = portfolio_service.get_position_allocation(
        db, portfolio_id, current_user.id
    )
    return [PositionAllocation(**a) for a in allocations]
