"""
User schemas
"""
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, Literal


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    """Google OAuth 登入請求"""
    id_token: str


class UserResponse(BaseModel):
    id: int
    email: str
    display_name: Optional[str]
    created_at: datetime
    auth_provider: str = 'local'
    avatar_url: Optional[str] = None
    subscription_tier: str = 'free'
    is_admin: bool = False

    class Config:
        from_attributes = True


class AdminUserResponse(BaseModel):
    """管理員查看用戶資訊（包含更多欄位）"""
    id: int
    email: str
    display_name: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    auth_provider: str
    google_id: Optional[str]
    avatar_url: Optional[str]
    subscription_tier: str
    is_admin: bool

    class Config:
        from_attributes = True


class UserSubscriptionUpdate(BaseModel):
    """更新用戶訂閱狀態"""
    subscription_tier: Literal['free', 'pro']


class UserAdminUpdate(BaseModel):
    """更新用戶管理員權限"""
    is_admin: bool


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
