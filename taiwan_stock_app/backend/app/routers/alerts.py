"""
價格警示路由
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Stock
from app.routers.auth import get_current_user
from app.schemas.alert import (
    PriceAlertCreate,
    PriceAlertUpdate,
    PriceAlertResponse,
    AlertTriggerInfo
)
from app.services.alert_service import alert_service

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=List[PriceAlertResponse])
def get_alerts(
    active_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得用戶的所有價格警示"""
    alerts = alert_service.get_user_alerts(db, current_user.id, active_only)

    # 補充股票名稱
    result = []
    for alert in alerts:
        stock = db.query(Stock).filter(Stock.stock_id == alert.stock_id).first()
        alert_data = PriceAlertResponse(
            id=alert.id,
            stock_id=alert.stock_id,
            stock_name=stock.name if stock else None,
            alert_type=alert.alert_type,
            target_price=alert.target_price,
            percent_threshold=alert.percent_threshold,
            is_active=alert.is_active,
            is_triggered=alert.is_triggered,
            triggered_at=alert.triggered_at,
            triggered_price=alert.triggered_price,
            notify_push=alert.notify_push,
            notify_email=alert.notify_email,
            notes=alert.notes,
            created_at=alert.created_at
        )
        result.append(alert_data)

    return result


@router.post("", response_model=PriceAlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(
    data: PriceAlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """建立新的價格警示"""
    try:
        alert = alert_service.create_alert(db, current_user.id, data)
        stock = db.query(Stock).filter(Stock.stock_id == alert.stock_id).first()

        return PriceAlertResponse(
            id=alert.id,
            stock_id=alert.stock_id,
            stock_name=stock.name if stock else None,
            alert_type=alert.alert_type,
            target_price=alert.target_price,
            percent_threshold=alert.percent_threshold,
            is_active=alert.is_active,
            is_triggered=alert.is_triggered,
            triggered_at=alert.triggered_at,
            triggered_price=alert.triggered_price,
            notify_push=alert.notify_push,
            notify_email=alert.notify_email,
            notes=alert.notes,
            created_at=alert.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{alert_id}", response_model=PriceAlertResponse)
def get_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得單一價格警示"""
    alert = alert_service.get_alert(db, current_user.id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="警示不存在")

    stock = db.query(Stock).filter(Stock.stock_id == alert.stock_id).first()

    return PriceAlertResponse(
        id=alert.id,
        stock_id=alert.stock_id,
        stock_name=stock.name if stock else None,
        alert_type=alert.alert_type,
        target_price=alert.target_price,
        percent_threshold=alert.percent_threshold,
        is_active=alert.is_active,
        is_triggered=alert.is_triggered,
        triggered_at=alert.triggered_at,
        triggered_price=alert.triggered_price,
        notify_push=alert.notify_push,
        notify_email=alert.notify_email,
        notes=alert.notes,
        created_at=alert.created_at
    )


@router.put("/{alert_id}", response_model=PriceAlertResponse)
def update_alert(
    alert_id: int,
    data: PriceAlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新價格警示"""
    alert = alert_service.update_alert(db, current_user.id, alert_id, data)
    if not alert:
        raise HTTPException(status_code=404, detail="警示不存在")

    stock = db.query(Stock).filter(Stock.stock_id == alert.stock_id).first()

    return PriceAlertResponse(
        id=alert.id,
        stock_id=alert.stock_id,
        stock_name=stock.name if stock else None,
        alert_type=alert.alert_type,
        target_price=alert.target_price,
        percent_threshold=alert.percent_threshold,
        is_active=alert.is_active,
        is_triggered=alert.is_triggered,
        triggered_at=alert.triggered_at,
        triggered_price=alert.triggered_price,
        notify_push=alert.notify_push,
        notify_email=alert.notify_email,
        notes=alert.notes,
        created_at=alert.created_at
    )


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """刪除價格警示"""
    success = alert_service.delete_alert(db, current_user.id, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="警示不存在")


@router.put("/{alert_id}/toggle", response_model=PriceAlertResponse)
def toggle_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切換警示啟用狀態"""
    alert = alert_service.toggle_alert(db, current_user.id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="警示不存在")

    stock = db.query(Stock).filter(Stock.stock_id == alert.stock_id).first()

    return PriceAlertResponse(
        id=alert.id,
        stock_id=alert.stock_id,
        stock_name=stock.name if stock else None,
        alert_type=alert.alert_type,
        target_price=alert.target_price,
        percent_threshold=alert.percent_threshold,
        is_active=alert.is_active,
        is_triggered=alert.is_triggered,
        triggered_at=alert.triggered_at,
        triggered_price=alert.triggered_price,
        notify_push=alert.notify_push,
        notify_email=alert.notify_email,
        notes=alert.notes,
        created_at=alert.created_at
    )


@router.put("/{alert_id}/reset", response_model=PriceAlertResponse)
def reset_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """重置警示狀態（重新啟用已觸發的警示）"""
    alert = alert_service.reset_alert(db, current_user.id, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="警示不存在")

    stock = db.query(Stock).filter(Stock.stock_id == alert.stock_id).first()

    return PriceAlertResponse(
        id=alert.id,
        stock_id=alert.stock_id,
        stock_name=stock.name if stock else None,
        alert_type=alert.alert_type,
        target_price=alert.target_price,
        percent_threshold=alert.percent_threshold,
        is_active=alert.is_active,
        is_triggered=alert.is_triggered,
        triggered_at=alert.triggered_at,
        triggered_price=alert.triggered_price,
        notify_push=alert.notify_push,
        notify_email=alert.notify_email,
        notes=alert.notes,
        created_at=alert.created_at
    )


@router.get("/triggered/list", response_model=List[PriceAlertResponse])
def get_triggered_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取得已觸發的警示列表"""
    alerts = alert_service.get_triggered_alerts(db, current_user.id)

    result = []
    for alert in alerts:
        stock = db.query(Stock).filter(Stock.stock_id == alert.stock_id).first()
        alert_data = PriceAlertResponse(
            id=alert.id,
            stock_id=alert.stock_id,
            stock_name=stock.name if stock else None,
            alert_type=alert.alert_type,
            target_price=alert.target_price,
            percent_threshold=alert.percent_threshold,
            is_active=alert.is_active,
            is_triggered=alert.is_triggered,
            triggered_at=alert.triggered_at,
            triggered_price=alert.triggered_price,
            notify_push=alert.notify_push,
            notify_email=alert.notify_email,
            notes=alert.notes,
            created_at=alert.created_at
        )
        result.append(alert_data)

    return result
