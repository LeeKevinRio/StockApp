"""
User schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal


class UserCreate(BaseModel):
    email: str  # 允許任意字串作為帳號，不限 email 格式
    password: str
    display_name: Optional[str] = None


class UserLogin(BaseModel):
    email: str  # 允許任意字串作為帳號
    password: str


class GoogleAuthRequest(BaseModel):
    """Google OAuth 登入請求 (ID Token)"""
    id_token: str


class GoogleAccessTokenRequest(BaseModel):
    """Google OAuth 登入請求 (Access Token) - 用於 Web 平台"""
    access_token: str
    email: str
    display_name: Optional[str] = None
    photo_url: Optional[str] = None


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
    last_login_at: Optional[datetime] = None

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
