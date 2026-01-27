"""
Portfolio Router
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.routers.auth import get_current_user
from app.models.user import User
from app.schemas.portfolio import (
    PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PortfolioHoldingCreate, PortfolioHoldingUpdate, PortfolioHoldingResponse,
    PortfolioSummary, PortfolioDetailResponse,
    PortfolioPerformance, PortfolioAllocationResponse
)
from app.services.portfolio_service import PortfolioService

router = APIRouter(prefix="/api/portfolio", tags=["portfolio"])


@router.get("", response_model=List[PortfolioSummary])
def get_portfolios(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得用戶所有投資組合摘要"""
    service = PortfolioService(db)
    return service.get_user_portfolios(current_user.id)


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(
    data: PortfolioCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """建立投資組合"""
    service = PortfolioService(db)
    return service.create_portfolio(current_user.id, data)


@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
def get_portfolio_detail(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得投資組合詳情"""
    service = PortfolioService(db)
    detail = service.get_portfolio_detail(portfolio_id, current_user.id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投資組合不存在"
        )
    return detail


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(
    portfolio_id: int,
    data: PortfolioUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新投資組合"""
    service = PortfolioService(db)
    portfolio = service.update_portfolio(portfolio_id, current_user.id, data)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投資組合不存在"
        )
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除投資組合"""
    service = PortfolioService(db)
    if not service.delete_portfolio(portfolio_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投資組合不存在"
        )


@router.post("/{portfolio_id}/holdings", response_model=PortfolioHoldingResponse, status_code=status.HTTP_201_CREATED)
def add_holding(
    portfolio_id: int,
    data: PortfolioHoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """新增持股"""
    service = PortfolioService(db)
    holding = service.add_holding(portfolio_id, current_user.id, data)
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投資組合不存在"
        )
    # 重新取得 enriched holding
    detail = service.get_portfolio_detail(portfolio_id, current_user.id)
    for h in detail.holdings:
        if h.id == holding.id:
            return h
    return holding


@router.put("/holdings/{holding_id}", response_model=PortfolioHoldingResponse)
def update_holding(
    holding_id: int,
    data: PortfolioHoldingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新持股"""
    service = PortfolioService(db)
    holding = service.update_holding(holding_id, current_user.id, data)
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="持股不存在"
        )
    # 取得 enriched holding
    detail = service.get_portfolio_detail(holding.portfolio_id, current_user.id)
    for h in detail.holdings:
        if h.id == holding.id:
            return h
    return holding


@router.delete("/holdings/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除持股"""
    service = PortfolioService(db)
    if not service.delete_holding(holding_id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="持股不存在"
        )


@router.get("/{portfolio_id}/performance", response_model=PortfolioPerformance)
def get_portfolio_performance(
    portfolio_id: int,
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得投資組合績效"""
    service = PortfolioService(db)
    performance = service.get_portfolio_performance(portfolio_id, current_user.id, days)
    if not performance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投資組合不存在"
        )
    return performance


@router.get("/{portfolio_id}/allocation", response_model=PortfolioAllocationResponse)
def get_portfolio_allocation(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得持股配置"""
    service = PortfolioService(db)
    allocation = service.get_portfolio_allocation(portfolio_id, current_user.id)
    if not allocation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投資組合不存在"
        )
    return allocation


@router.post("/{portfolio_id}/snapshot", status_code=status.HTTP_201_CREATED)
def take_snapshot(
    portfolio_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """建立組合快照"""
    service = PortfolioService(db)
    snapshot = service.take_snapshot(portfolio_id, current_user.id)
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="投資組合不存在"
        )
    return {"message": "快照建立成功", "date": snapshot.date}
