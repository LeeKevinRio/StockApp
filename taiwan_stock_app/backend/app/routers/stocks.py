"""
Stocks router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Stock
from app.schemas import StockDetail, StockPrice, StockHistory
from app.services import StockDataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/stocks", tags=["stocks"])
stock_service = StockDataService()


@router.get("/search", response_model=List[StockDetail])
def search_stocks(
    q: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """搜尋股票"""
    stocks = stock_service.search_stocks(db, q)
    return stocks


@router.get("/{stock_id}", response_model=StockDetail)
def get_stock_detail(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得股票詳情"""
    stock = stock_service.get_stock(db, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")
    return stock


@router.get("/{stock_id}/price", response_model=StockPrice)
def get_stock_price(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得即時報價"""
    price_data = stock_service.get_realtime_price(stock_id)
    if not price_data:
        raise HTTPException(status_code=404, detail="Price data not available")

    # Get stock name
    stock = stock_service.get_stock(db, stock_id)
    if stock:
        price_data["name"] = stock.name

    return price_data


@router.get("/{stock_id}/history", response_model=List[StockHistory])
def get_stock_history(
    stock_id: str,
    days: int = 60,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得歷史K線"""
    history = stock_service.get_history(db, stock_id, days)
    return history
