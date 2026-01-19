"""
Watchlist router
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal

from app.database import get_db
from app.models import User, Watchlist, Stock
from app.schemas import WatchlistItem, WatchlistAdd
from app.services import StockDataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])
stock_service = StockDataService()


@router.get("", response_model=List[WatchlistItem])
def get_watchlist(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得自選股列表"""
    watchlist_items = (
        db.query(Watchlist, Stock)
        .join(Stock, Watchlist.stock_id == Stock.stock_id)
        .filter(Watchlist.user_id == current_user.id)
        .all()
    )

    results = []
    for watchlist, stock in watchlist_items:
        # Get realtime price
        price_data = stock_service.get_realtime_price(stock.stock_id)
        if price_data:
            results.append(
                WatchlistItem(
                    stock_id=stock.stock_id,
                    name=stock.name,
                    current_price=price_data["current_price"],
                    change_percent=price_data["change_percent"],
                    added_at=watchlist.added_at,
                    notes=watchlist.notes,
                )
            )

    return results


@router.post("")
def add_to_watchlist(
    data: WatchlistAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增自選股"""
    # Check if stock exists
    stock = db.query(Stock).filter(Stock.stock_id == data.stock_id).first()
    if not stock:
        raise HTTPException(status_code=404, detail="Stock not found")

    # Check if already in watchlist
    existing = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == current_user.id,
            Watchlist.stock_id == data.stock_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="Stock already in watchlist")

    # Add to watchlist
    watchlist_item = Watchlist(
        user_id=current_user.id,
        stock_id=data.stock_id,
        notes=data.notes,
    )
    db.add(watchlist_item)
    db.commit()

    return {"message": "Added to watchlist successfully"}


@router.delete("/{stock_id}")
def remove_from_watchlist(
    stock_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刪除自選股"""
    watchlist_item = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == current_user.id,
            Watchlist.stock_id == stock_id,
        )
        .first()
    )

    if not watchlist_item:
        raise HTTPException(status_code=404, detail="Stock not in watchlist")

    db.delete(watchlist_item)
    db.commit()

    return {"message": "Removed from watchlist successfully"}
