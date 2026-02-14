"""
Watchlist router - 支援台股(TW)與美股(US)，含分組功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from pydantic import BaseModel

from app.database import get_db
from app.models import User, Watchlist, WatchlistGroup, Stock
from app.schemas import WatchlistItem, WatchlistAdd
from app.services import StockDataService
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])
stock_service = StockDataService()


# ---- Watchlist Group schemas ----

class GroupCreate(BaseModel):
    name: str
    color: Optional[str] = "#2196F3"

class GroupUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None
    sort_order: Optional[int] = None

class StockGroupAssign(BaseModel):
    group_id: Optional[int] = None  # None = 移出分組


@router.get("")
def get_watchlist(
    market: Optional[str] = Query(None, description="Filter by market: TW or US"),
    force_refresh: bool = Query(False, description="Force refresh cache"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得自選股列表（優化版本：批量獲取報價）

    Args:
        market: 市場過濾 - "TW"(台股), "US"(美股), None(全部)
        force_refresh: 是否強制清除快取
    """
    if force_refresh:
        from app.services.stock_data_service import _price_cache
        _price_cache.clear()
    # Build query
    query = db.query(Watchlist, Stock).join(
        Stock, Watchlist.stock_id == Stock.stock_id
    ).filter(Watchlist.user_id == current_user.id)

    # Apply market filter if specified
    if market:
        query = query.filter(Stock.market_region == market)

    watchlist_items = query.all()

    if not watchlist_items:
        return []

    # 分離台股和美股
    tw_stocks = []
    us_stocks = []
    stock_info_map = {}  # stock_id -> (watchlist, stock)

    for watchlist, stock in watchlist_items:
        market_region = getattr(stock, 'market_region', 'TW') or 'TW'
        stock_info_map[stock.stock_id] = (watchlist, stock, market_region)

        if market_region == "US":
            us_stocks.append(stock.stock_id)
        else:
            tw_stocks.append(stock.stock_id)

    # 批量獲取報價
    tw_prices = stock_service.get_realtime_prices_batch(tw_stocks, market="TW") if tw_stocks else {}
    us_prices = stock_service.get_realtime_prices_batch(us_stocks, market="US") if us_stocks else {}

    # 合併報價數據
    all_prices = {**tw_prices, **us_prices}

    # 構建結果
    results = []
    for stock_id, (watchlist, stock, market_region) in stock_info_map.items():
        price_data = all_prices.get(stock_id)

        if price_data:
            results.append({
                "stock_id": stock.stock_id,
                "name": stock.name,
                "current_price": float(price_data["current_price"]),
                "change_percent": float(price_data["change_percent"]),
                "added_at": watchlist.added_at.isoformat() if watchlist.added_at else None,
                "notes": watchlist.notes,
                "market_region": market_region,
                "currency": price_data.get("currency", "TWD"),
            })
        else:
            # 即使沒有報價也返回基本資訊
            results.append({
                "stock_id": stock.stock_id,
                "name": stock.name,
                "current_price": 0,
                "change_percent": 0,
                "added_at": watchlist.added_at.isoformat() if watchlist.added_at else None,
                "notes": watchlist.notes,
                "market_region": market_region,
                "currency": "TWD" if market_region == "TW" else "USD",
            })

    return results


@router.post("")
def add_to_watchlist(
    data: WatchlistAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增自選股（支援台股與美股）"""
    market = getattr(data, 'market', 'TW') or 'TW'

    # Check if stock exists
    stock = db.query(Stock).filter(Stock.stock_id == data.stock_id).first()

    if not stock:
        # For US stocks, create a new stock record if it doesn't exist
        if market == "US":
            stock_info = stock_service.get_stock(db, data.stock_id, market="US")
            if not stock_info:
                raise HTTPException(status_code=404, detail="Stock not found")

            # Create new stock record for US stock
            stock = Stock(
                stock_id=data.stock_id,
                name=stock_info.get("name", data.stock_id),
                english_name=stock_info.get("long_name", ""),
                industry=stock_info.get("industry", ""),
                sector=stock_info.get("sector", ""),
                market=stock_info.get("exchange", "NYSE"),
                market_region="US",
            )
            db.add(stock)
            db.commit()
            db.refresh(stock)
        else:
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


# ==================== 自選股分組 ====================

@router.get("/groups")
def get_watchlist_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得使用者的自選股分組"""
    groups = (
        db.query(WatchlistGroup)
        .filter(WatchlistGroup.user_id == current_user.id)
        .order_by(WatchlistGroup.sort_order, WatchlistGroup.id)
        .all()
    )
    return [
        {
            "id": g.id,
            "name": g.name,
            "color": g.color,
            "sort_order": g.sort_order,
            "stock_count": db.query(Watchlist).filter(
                Watchlist.user_id == current_user.id,
                Watchlist.group_id == g.id,
            ).count(),
        }
        for g in groups
    ]


@router.post("/groups")
def create_watchlist_group(
    data: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """建立自選股分組"""
    # 限制最多 10 個分組
    count = db.query(WatchlistGroup).filter(
        WatchlistGroup.user_id == current_user.id
    ).count()
    if count >= 10:
        raise HTTPException(status_code=400, detail="最多只能建立 10 個分組")

    group = WatchlistGroup(
        user_id=current_user.id,
        name=data.name,
        color=data.color,
        sort_order=count,
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    return {
        "id": group.id,
        "name": group.name,
        "color": group.color,
        "sort_order": group.sort_order,
    }


@router.put("/groups/{group_id}")
def update_watchlist_group(
    group_id: int,
    data: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新自選股分組"""
    group = (
        db.query(WatchlistGroup)
        .filter(WatchlistGroup.id == group_id, WatchlistGroup.user_id == current_user.id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="分組不存在")

    if data.name is not None:
        group.name = data.name
    if data.color is not None:
        group.color = data.color
    if data.sort_order is not None:
        group.sort_order = data.sort_order

    db.commit()
    return {"message": "分組已更新"}


@router.delete("/groups/{group_id}")
def delete_watchlist_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刪除自選股分組（股票會回到未分組）"""
    group = (
        db.query(WatchlistGroup)
        .filter(WatchlistGroup.id == group_id, WatchlistGroup.user_id == current_user.id)
        .first()
    )
    if not group:
        raise HTTPException(status_code=404, detail="分組不存在")

    # 將該分組下的股票移回未分組
    db.query(Watchlist).filter(
        Watchlist.user_id == current_user.id,
        Watchlist.group_id == group_id,
    ).update({"group_id": None})

    db.delete(group)
    db.commit()
    return {"message": "分組已刪除"}


@router.put("/{stock_id}/group")
def assign_stock_to_group(
    stock_id: str,
    data: StockGroupAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """將股票指定到分組"""
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

    # 驗證分組存在
    if data.group_id is not None:
        group = db.query(WatchlistGroup).filter(
            WatchlistGroup.id == data.group_id,
            WatchlistGroup.user_id == current_user.id,
        ).first()
        if not group:
            raise HTTPException(status_code=404, detail="分組不存在")

    watchlist_item.group_id = data.group_id
    db.commit()
    return {"message": "已更新分組"}
