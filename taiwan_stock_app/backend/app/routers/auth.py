"""
Authentication router
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer
from fastapi.security.http import HTTPAuthorizationCredentials

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, Token, UserResponse, GoogleAuthRequest, GoogleAccessTokenRequest
from app.config import settings
from app.auth_secret import get_jwt_secret
from app.services.oauth_service import oauth_service
from app.rate_limit import limiter

router = APIRouter(prefix="/api/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    """Hash password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int) -> str:
    """Create JWT access token"""
    to_encode = {"sub": str(user_id)}
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, get_jwt_secret(), algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[settings.JWT_ALGORITHM])
        user_id_str: str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        user_id = int(user_id_str)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Get current user and verify admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


def _check_email_whitelist(email: str):
    """檢查 email 是否在白名單中（正式開放前限制登入）"""
    if settings.ALLOWED_EMAILS and email not in settings.ALLOWED_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="目前僅開放特定帳號登入，正式上線後將開放註冊"
        )


def _update_last_login(user: User, db: Session):
    """更新使用者最後登入時間"""
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)


@router.post("/register", response_model=Token)
@limiter.limit("5/minute")
def register(request: Request, user_data: UserCreate, db: Session = Depends(get_db)):
    """Register new user（正式開放前暫停）"""
    # 正式開放前禁止帳號密碼註冊
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="註冊功能尚未開放，請使用 Google 帳號登入"
    )


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user（正式開放前暫停）"""
    # 正式開放前禁止帳號密碼登入
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="帳號密碼登入尚未開放，請使用 Google 帳號登入"
    )


@router.post("/google", response_model=Token)
@limiter.limit("10/minute")
def google_auth(request: Request, auth_data: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Google OAuth 登入"""
    # Verify Google token
    google_user = oauth_service.verify_google_token(auth_data.id_token)
    if not google_user:
        raise HTTPException(status_code=401, detail="Invalid Google token")

    # 白名單檢查
    _check_email_whitelist(google_user['email'])

    # Check if user exists by google_id
    user = db.query(User).filter(User.google_id == google_user['google_id']).first()

    if not user:
        # Check if user exists by email (might have registered with email/password before)
        user = db.query(User).filter(User.email == google_user['email']).first()

        if user:
            # Link Google account to existing user
            user.google_id = google_user['google_id']
            user.auth_provider = 'google'
            if not user.avatar_url and google_user.get('picture'):
                user.avatar_url = google_user['picture']
            if not user.display_name and google_user.get('name'):
                user.display_name = google_user['name']
        else:
            # Create new user
            user = User(
                email=google_user['email'],
                google_id=google_user['google_id'],
                display_name=google_user.get('name', ''),
                avatar_url=google_user.get('picture', ''),
                auth_provider='google',
            )
            db.add(user)

        db.commit()
        db.refresh(user)

    # 更新最後登入時間
    _update_last_login(user, db)

    # Create access token
    access_token = create_access_token(user.id)

    return Token(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
            auth_provider=user.auth_provider,
            avatar_url=user.avatar_url,
            subscription_tier=user.subscription_tier,
            is_admin=user.is_admin,
        ),
    )


@router.post("/google-access-token", response_model=Token)
@limiter.limit("10/minute")
def google_auth_with_access_token(request: Request, token_data: GoogleAccessTokenRequest, db: Session = Depends(get_db)):
    """Google OAuth 登入 (使用 Access Token) - 用於 Web 平台"""
    import hashlib

    # 白名單檢查
    _check_email_whitelist(token_data.email)

    # 使用 email 作為唯一識別 (因為 Web 無法取得 google_id)
    # 產生一個基於 email 的偽 google_id
    google_id = hashlib.sha256(f"google_{token_data.email}".encode()).hexdigest()[:32]

    # Check if user exists by google_id
    user = db.query(User).filter(User.google_id == google_id).first()

    if not user:
        # Check if user exists by email
        user = db.query(User).filter(User.email == token_data.email).first()

        if user:
            # Link Google account to existing user
            user.google_id = google_id
            user.auth_provider = 'google'
            if not user.avatar_url and token_data.photo_url:
                user.avatar_url = token_data.photo_url
            if not user.display_name and token_data.display_name:
                user.display_name = token_data.display_name
        else:
            # Create new user
            user = User(
                email=token_data.email,
                google_id=google_id,
                display_name=token_data.display_name or '',
                avatar_url=token_data.photo_url or '',
                auth_provider='google',
            )
            db.add(user)

        db.commit()
        db.refresh(user)

    # 更新最後登入時間
    _update_last_login(user, db)

    # Create access token
    access_token = create_access_token(user.id)

    return Token(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            created_at=user.created_at,
            auth_provider=user.auth_provider,
            avatar_url=user.avatar_url,
            subscription_tier=user.subscription_tier,
            is_admin=user.is_admin,
        ),
    )


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        created_at=current_user.created_at,
        auth_provider=current_user.auth_provider,
        avatar_url=current_user.avatar_url,
        subscription_tier=current_user.subscription_tier,
        is_admin=current_user.is_admin,
    )


@router.delete("/account")
def delete_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """刪除使用者帳號及所有關聯資料（Apple App Store 要求完整資料刪除）"""
    from app.models import (
        Portfolio, Position, Transaction, AIReport, AIChatHistory,
        PriceAlert, Watchlist, WatchlistGroup,
        TradingDiaryEntry, VirtualAccount, VirtualPosition, VirtualOrder,
        BrokerAccount, BrokerPosition, UserAIConfig, AIUsageDaily,
    )

    user_id = current_user.id

    # 刪除所有關聯資料（按外鍵依賴順序）
    # 投資組合相關
    portfolios = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    for p in portfolios:
        db.query(Transaction).filter(Transaction.portfolio_id == p.id).delete()
        db.query(Position).filter(Position.portfolio_id == p.id).delete()
    db.query(Portfolio).filter(Portfolio.user_id == user_id).delete()

    # AI 相關
    db.query(AIReport).filter(AIReport.user_id == user_id).delete()
    db.query(AIChatHistory).filter(AIChatHistory.user_id == user_id).delete()
    db.query(AIUsageDaily).filter(AIUsageDaily.user_id == user_id).delete()
    db.query(UserAIConfig).filter(UserAIConfig.user_id == user_id).delete()

    # 自選股
    db.query(Watchlist).filter(Watchlist.user_id == user_id).delete()
    db.query(WatchlistGroup).filter(WatchlistGroup.user_id == user_id).delete()

    # 警示
    db.query(PriceAlert).filter(PriceAlert.user_id == user_id).delete()

    # 交易日記
    db.query(TradingDiaryEntry).filter(TradingDiaryEntry.user_id == user_id).delete()

    # 模擬交易
    accounts = db.query(VirtualAccount).filter(VirtualAccount.user_id == user_id).all()
    for acc in accounts:
        db.query(VirtualOrder).filter(VirtualOrder.account_id == acc.id).delete()
        db.query(VirtualPosition).filter(VirtualPosition.account_id == acc.id).delete()
    db.query(VirtualAccount).filter(VirtualAccount.user_id == user_id).delete()

    # 券商
    broker_accounts = db.query(BrokerAccount).filter(BrokerAccount.user_id == user_id).all()
    for ba in broker_accounts:
        db.query(BrokerPosition).filter(BrokerPosition.broker_account_id == ba.id).delete()
    db.query(BrokerAccount).filter(BrokerAccount.user_id == user_id).delete()

    # 刪除使用者
    db.delete(current_user)
    db.commit()

    return {"message": "帳號已成功刪除"}
