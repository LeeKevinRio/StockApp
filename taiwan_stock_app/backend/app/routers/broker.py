"""
Broker Router — 券商帳戶連動 API
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.routers.auth import get_current_user
from app.schemas.broker import (
    LinkAccountRequest,
    Verify2FARequest,
    LinkAccountResponse,
    BrokerStatusResponse,
    BrokerPositionResponse,
    BrokerPositionListResponse,
)
from app.services.firstrade_service import firstrade_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/broker", tags=["broker"])


@router.post("/link", response_model=LinkAccountResponse)
def link_broker_account(
    req: LinkAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """連結券商帳戶"""
    result = firstrade_service.link_account(
        db, current_user.id, req.username, req.password, req.pin,
    )
    return LinkAccountResponse(**result)


@router.post("/verify-2fa", response_model=LinkAccountResponse)
def verify_2fa(
    req: Verify2FARequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """驗證 2FA 碼"""
    result = firstrade_service.verify_2fa(
        db, current_user.id, req.account_id, req.code,
    )
    return LinkAccountResponse(**result)


@router.get("/status", response_model=BrokerStatusResponse)
def get_broker_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """查詢券商連結狀態"""
    return firstrade_service.get_status(db, current_user.id)


@router.get("/positions", response_model=BrokerPositionListResponse)
def get_broker_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得券商持倉列表"""
    positions = firstrade_service.get_positions(db, current_user.id)
    return BrokerPositionListResponse(
        positions=[BrokerPositionResponse.model_validate(p) for p in positions],
        total=len(positions),
    )


@router.post("/sync")
def sync_broker_positions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """手動觸發持倉同步"""
    result = firstrade_service.sync_positions(db, current_user.id)
    if not result.get("synced"):
        raise HTTPException(status_code=400, detail=result.get("message", "同步失敗"))
    return result


@router.delete("/unlink")
def unlink_broker(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """解除券商連結"""
    result = firstrade_service.unlink(db, current_user.id)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message", "解除連結失敗"))
    return result
