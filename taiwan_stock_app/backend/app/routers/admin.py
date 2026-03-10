"""
Admin router - 管理員功能
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas import AdminUserResponse, UserSubscriptionUpdate, UserAdminUpdate
from app.routers.auth import get_admin_user

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users", response_model=List[AdminUserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """列出所有用戶（僅管理員），依最後登入時間排序"""
    users = db.query(User).order_by(User.last_login_at.desc().nullslast()).offset(skip).limit(limit).all()
    return [
        AdminUserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
            updated_at=user.updated_at,
            auth_provider=user.auth_provider or 'local',
            google_id=user.google_id,
            avatar_url=user.avatar_url,
            subscription_tier=user.subscription_tier or 'free',
            is_admin=user.is_admin or False,
            last_login_at=user.last_login_at,
        )
        for user in users
    ]


@router.get("/users/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """取得特定用戶資訊（僅管理員）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
        auth_provider=user.auth_provider or 'local',
        google_id=user.google_id,
        avatar_url=user.avatar_url,
        subscription_tier=user.subscription_tier or 'free',
        is_admin=user.is_admin or False,
        last_login_at=user.last_login_at,
    )


@router.patch("/users/{user_id}/subscription", response_model=AdminUserResponse)
def update_user_subscription(
    user_id: int,
    update_data: UserSubscriptionUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """更新用戶訂閱狀態（僅管理員）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.subscription_tier = update_data.subscription_tier
    db.commit()
    db.refresh(user)

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
        auth_provider=user.auth_provider or 'local',
        google_id=user.google_id,
        avatar_url=user.avatar_url,
        subscription_tier=user.subscription_tier or 'free',
        is_admin=user.is_admin or False,
        last_login_at=user.last_login_at,
    )


@router.patch("/users/{user_id}/admin", response_model=AdminUserResponse)
def update_user_admin_status(
    user_id: int,
    update_data: UserAdminUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """設定用戶管理員權限（僅管理員）"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Prevent admin from removing their own admin rights
    if user.id == admin_user.id and not update_data.is_admin:
        raise HTTPException(
            status_code=400,
            detail="Cannot remove your own admin privileges"
        )

    user.is_admin = update_data.is_admin
    db.commit()
    db.refresh(user)

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        created_at=user.created_at,
        updated_at=user.updated_at,
        auth_provider=user.auth_provider or 'local',
        google_id=user.google_id,
        avatar_url=user.avatar_url,
        subscription_tier=user.subscription_tier or 'free',
        is_admin=user.is_admin or False,
        last_login_at=user.last_login_at,
    )


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user),
):
    """取得管理員統計資訊（含活躍度）"""
    total_users = db.query(User).count()
    pro_users = db.query(User).filter(User.subscription_tier == 'pro').count()
    free_users = db.query(User).filter(User.subscription_tier == 'free').count()
    google_users = db.query(User).filter(User.auth_provider == 'google').count()
    local_users = db.query(User).filter(User.auth_provider == 'local').count()

    # 活躍度統計
    now = datetime.utcnow()
    active_today = db.query(User).filter(
        User.last_login_at >= now - timedelta(days=1)
    ).count()
    active_7d = db.query(User).filter(
        User.last_login_at >= now - timedelta(days=7)
    ).count()
    active_30d = db.query(User).filter(
        User.last_login_at >= now - timedelta(days=30)
    ).count()

    return {
        "total_users": total_users,
        "pro_users": pro_users,
        "free_users": free_users,
        "google_users": google_users,
        "local_users": local_users,
        "active_today": active_today,
        "active_7d": active_7d,
        "active_30d": active_30d,
    }
