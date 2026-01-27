"""
模擬交易路由
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas.trading import OrderCreate, AccountSummary, TradeResult
from app.services.trading_service import trading_service
from app.routers.auth import get_current_user

router = APIRouter(prefix="/api/trading", tags=["trading"])


@router.get("/account")
def get_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得虛擬交易帳戶資訊

    Returns:
        帳戶摘要，包含資金、持倉、近期訂單
    """
    try:
        return trading_service.get_account_summary(db, current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取帳戶失敗: {str(e)}")


@router.post("/order")
def place_order(
    order: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    下單

    Args:
        order: 訂單資訊 (stock_id, order_type, quantity, price)

    Returns:
        交易結果
    """
    try:
        result = trading_service.place_order(
            db=db,
            user_id=current_user.id,
            stock_id=order.stock_id,
            order_type=order.order_type,
            quantity=order.quantity,
            price=order.price
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下單失敗: {str(e)}")


@router.delete("/order/{order_id}")
def cancel_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取消訂單

    Args:
        order_id: 訂單ID

    Returns:
        取消結果
    """
    try:
        result = trading_service.cancel_order(db, current_user.id, order_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消訂單失敗: {str(e)}")


@router.post("/reset")
def reset_account(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    重置帳戶

    清除所有持倉和訂單，將資金恢復到初始狀態

    Returns:
        重置結果
    """
    try:
        result = trading_service.reset_account(db, current_user.id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重置帳戶失敗: {str(e)}")


@router.get("/positions")
def get_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得持倉列表

    Returns:
        持倉列表
    """
    try:
        summary = trading_service.get_account_summary(db, current_user.id)
        return {'positions': summary['positions']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取持倉失敗: {str(e)}")


@router.get("/orders")
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    取得訂單歷史

    Returns:
        訂單列表
    """
    try:
        summary = trading_service.get_account_summary(db, current_user.id)
        return {'orders': summary['recent_orders']}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"獲取訂單失敗: {str(e)}")
