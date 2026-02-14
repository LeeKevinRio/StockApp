"""
交易日記 API
GET  /api/diary       - 取得日記列表
POST /api/diary       - 新增日記
PUT  /api/diary/{id}  - 更新日記
DELETE /api/diary/{id} - 刪除日記
GET  /api/diary/stats  - 統計數據
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.models import User
from app.models.trading_diary import TradingDiaryEntry
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/diary", tags=["Trading Diary"])


class DiaryCreate(BaseModel):
    stock_id: Optional[str] = None
    trade_type: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    emotion: Optional[str] = None
    strategy: Optional[str] = None
    notes: Optional[str] = None
    lesson_learned: Optional[str] = None
    tags: Optional[str] = None
    rating: Optional[int] = None


class DiaryUpdate(BaseModel):
    stock_id: Optional[str] = None
    trade_type: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    emotion: Optional[str] = None
    strategy: Optional[str] = None
    notes: Optional[str] = None
    lesson_learned: Optional[str] = None
    tags: Optional[str] = None
    rating: Optional[int] = None


def _entry_to_dict(entry: TradingDiaryEntry) -> dict:
    return {
        "id": entry.id,
        "stock_id": entry.stock_id,
        "trade_date": entry.trade_date.isoformat() if entry.trade_date else None,
        "trade_type": entry.trade_type,
        "price": entry.price,
        "quantity": entry.quantity,
        "pnl": entry.pnl,
        "pnl_percent": entry.pnl_percent,
        "emotion": entry.emotion,
        "strategy": entry.strategy,
        "notes": entry.notes,
        "lesson_learned": entry.lesson_learned,
        "tags": entry.tags,
        "rating": entry.rating,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


@router.get("")
def get_diary_entries(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    stock_id: Optional[str] = Query(None),
    trade_type: Optional[str] = Query(None),
    emotion: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得交易日記列表"""
    query = db.query(TradingDiaryEntry).filter(
        TradingDiaryEntry.user_id == current_user.id
    )

    if stock_id:
        query = query.filter(TradingDiaryEntry.stock_id == stock_id)
    if trade_type:
        query = query.filter(TradingDiaryEntry.trade_type == trade_type)
    if emotion:
        query = query.filter(TradingDiaryEntry.emotion == emotion)

    total = query.count()
    entries = query.order_by(TradingDiaryEntry.trade_date.desc()).offset(offset).limit(limit).all()

    return {
        "total": total,
        "entries": [_entry_to_dict(e) for e in entries],
    }


@router.post("")
def create_diary_entry(
    data: DiaryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """新增交易日記"""
    entry = TradingDiaryEntry(
        user_id=current_user.id,
        stock_id=data.stock_id,
        trade_type=data.trade_type,
        price=data.price,
        quantity=data.quantity,
        pnl=data.pnl,
        pnl_percent=data.pnl_percent,
        emotion=data.emotion,
        strategy=data.strategy,
        notes=data.notes,
        lesson_learned=data.lesson_learned,
        tags=data.tags,
        rating=data.rating,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return _entry_to_dict(entry)


@router.put("/{entry_id}")
def update_diary_entry(
    entry_id: int,
    data: DiaryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新交易日記"""
    entry = (
        db.query(TradingDiaryEntry)
        .filter(TradingDiaryEntry.id == entry_id, TradingDiaryEntry.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="日記不存在")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return _entry_to_dict(entry)


@router.delete("/{entry_id}")
def delete_diary_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刪除交易日記"""
    entry = (
        db.query(TradingDiaryEntry)
        .filter(TradingDiaryEntry.id == entry_id, TradingDiaryEntry.user_id == current_user.id)
        .first()
    )
    if not entry:
        raise HTTPException(status_code=404, detail="日記不存在")

    db.delete(entry)
    db.commit()
    return {"message": "日記已刪除"}


@router.get("/stats")
def get_diary_stats(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得交易日記統計"""
    from datetime import timedelta

    cutoff = datetime.now() - timedelta(days=days)

    entries = (
        db.query(TradingDiaryEntry)
        .filter(
            TradingDiaryEntry.user_id == current_user.id,
            TradingDiaryEntry.trade_date >= cutoff,
        )
        .all()
    )

    total_entries = len(entries)
    buy_count = sum(1 for e in entries if e.trade_type == 'buy')
    sell_count = sum(1 for e in entries if e.trade_type == 'sell')

    # 盈虧統計
    pnl_entries = [e for e in entries if e.pnl is not None]
    total_pnl = sum(e.pnl for e in pnl_entries) if pnl_entries else 0
    win_count = sum(1 for e in pnl_entries if e.pnl > 0)
    loss_count = sum(1 for e in pnl_entries if e.pnl < 0)

    # 情緒統計
    emotion_counts = {}
    for e in entries:
        if e.emotion:
            emotion_counts[e.emotion] = emotion_counts.get(e.emotion, 0) + 1

    # 評分統計
    rated = [e.rating for e in entries if e.rating is not None]
    avg_rating = sum(rated) / len(rated) if rated else 0

    return {
        "days": days,
        "total_entries": total_entries,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "total_pnl": round(total_pnl, 2),
        "win_count": win_count,
        "loss_count": loss_count,
        "win_rate": round(win_count / len(pnl_entries) * 100, 1) if pnl_entries else 0,
        "emotion_distribution": emotion_counts,
        "avg_rating": round(avg_rating, 1),
    }
