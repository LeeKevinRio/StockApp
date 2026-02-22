"""
AI 配額依賴 — per-user daily AI call limit
Admin / BYOK 用戶不受限，Free 10 次/天，Pro 50 次/天
"""

from dataclasses import dataclass, field
from datetime import date

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.ai_usage import AIUsageDaily
from app.models.user_ai_config import UserAIConfig
from app.routers.auth import get_current_user

DAILY_LIMITS = {
    "free": 10,
    "pro": 50,
}


@dataclass
class AIQuotaContext:
    """配額上下文：endpoint 在實際呼叫 AI 前呼叫 ensure_available()，成功後呼叫 increment()"""
    db: Session
    user_id: int
    daily_limit: int  # 0 = unlimited
    used: int = 0
    is_unlimited: bool = False
    _usage_row: object = field(default=None, repr=False)

    @property
    def remaining(self) -> int:
        if self.is_unlimited:
            return -1  # -1 代表無限
        return max(0, self.daily_limit - self.used)

    def ensure_available(self):
        """在實際呼叫 AI 前檢查配額，超額 raise 429"""
        if self.is_unlimited:
            return
        if self.used >= self.daily_limit:
            raise HTTPException(
                status_code=429,
                detail=f"今日 AI 使用次數已達上限 ({self.daily_limit} 次)。明天將自動重置，或升級方案以取得更多額度。",
            )

    def increment(self):
        """AI 呼叫成功後遞增計數"""
        if self.is_unlimited:
            return
        if self._usage_row is None:
            self._usage_row = _get_or_create_usage_row(self.db, self.user_id)
        self._usage_row.call_count += 1
        self.used = self._usage_row.call_count
        self.db.commit()

    def to_dict(self) -> dict:
        return {
            "daily_limit": self.daily_limit if not self.is_unlimited else None,
            "used": self.used,
            "remaining": self.remaining,
            "is_unlimited": self.is_unlimited,
        }


def _get_or_create_usage_row(db: Session, user_id: int) -> AIUsageDaily:
    """取得或建立今天的用量記錄"""
    today = date.today()
    row = (
        db.query(AIUsageDaily)
        .filter(AIUsageDaily.user_id == user_id, AIUsageDaily.usage_date == today)
        .first()
    )
    if row is None:
        row = AIUsageDaily(user_id=user_id, usage_date=today, call_count=0)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def check_ai_quota(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AIQuotaContext:
    """FastAPI 依賴：回傳 AIQuotaContext，不直接 raise（讓 endpoint 決定何時檢查）"""
    # Admin → 無限
    if current_user.is_admin:
        return AIQuotaContext(db=db, user_id=current_user.id, daily_limit=0, is_unlimited=True)

    # BYOK 用戶（有 user_ai_configs 記錄）→ 無限
    has_byok = (
        db.query(UserAIConfig.id)
        .filter(UserAIConfig.user_id == current_user.id)
        .first()
    )
    if has_byok:
        return AIQuotaContext(db=db, user_id=current_user.id, daily_limit=0, is_unlimited=True)

    # 一般用戶：根據 subscription_tier 決定上限
    tier = getattr(current_user, "subscription_tier", "free") or "free"
    daily_limit = DAILY_LIMITS.get(tier, DAILY_LIMITS["free"])

    usage_row = _get_or_create_usage_row(db, current_user.id)
    return AIQuotaContext(
        db=db,
        user_id=current_user.id,
        daily_limit=daily_limit,
        used=usage_row.call_count,
        is_unlimited=False,
        _usage_row=usage_row,
    )
