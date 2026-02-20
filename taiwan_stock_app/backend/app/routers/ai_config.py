"""
AI Config Router — BYOK AI 設定端點
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.models.user_ai_config import UserAIConfig
from app.routers.auth import get_current_user
from app.services.crypto_service import encrypt_credentials, decrypt_credentials
from app.services.ai_client_factory import AIClientFactory
from app.schemas.ai_config import (
    AI_PROVIDERS,
    AIConfigSave,
    AIConfigResponse,
    AIConfigTestRequest,
    AIProvidersResponse,
    AIProviderInfo,
    AIModelInfo,
)
from app.rate_limit import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-config", tags=["ai-config"])


@router.get("/providers", response_model=AIProvidersResponse)
def get_providers():
    """回傳可用的 AI provider + model 清單"""
    providers = []
    for pid, info in AI_PROVIDERS.items():
        models = [AIModelInfo(id=m, label=m) for m in info["models"]]
        providers.append(AIProviderInfo(id=pid, label=info["label"], models=models))
    return AIProvidersResponse(providers=providers)


@router.get("", response_model=AIConfigResponse)
def get_ai_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """取得用戶當前 AI 配置"""
    record = db.query(UserAIConfig).filter(
        UserAIConfig.user_id == current_user.id
    ).first()

    if not record:
        return AIConfigResponse(has_api_key=False)

    provider_label = AI_PROVIDERS.get(record.provider, {}).get("label", record.provider)
    return AIConfigResponse(
        provider=record.provider,
        model=record.model,
        has_api_key=True,
        provider_label=provider_label,
    )


@router.post("", response_model=AIConfigResponse)
def save_ai_config(
    payload: AIConfigSave,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """儲存/更新用戶 AI 配置（加密 API Key）"""
    # 驗證 model 屬於該 provider
    provider_models = AI_PROVIDERS.get(payload.provider, {}).get("models", [])
    if payload.model not in provider_models:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{payload.model}' 不屬於 provider '{payload.provider}'",
        )

    encrypted = encrypt_credentials({"api_key": payload.api_key})

    record = db.query(UserAIConfig).filter(
        UserAIConfig.user_id == current_user.id
    ).first()

    if record:
        record.provider = payload.provider
        record.model = payload.model
        record.encrypted_api_key = encrypted
    else:
        record = UserAIConfig(
            user_id=current_user.id,
            provider=payload.provider,
            model=payload.model,
            encrypted_api_key=encrypted,
        )
        db.add(record)

    db.commit()
    logger.info(f"User {current_user.id} saved AI config: {payload.provider}/{payload.model}")

    provider_label = AI_PROVIDERS.get(payload.provider, {}).get("label", payload.provider)
    return AIConfigResponse(
        provider=payload.provider,
        model=payload.model,
        has_api_key=True,
        provider_label=provider_label,
    )


@router.delete("")
def delete_ai_config(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """刪除用戶 AI 配置（恢復使用系統預設）"""
    deleted = db.query(UserAIConfig).filter(
        UserAIConfig.user_id == current_user.id
    ).delete()
    db.commit()

    if deleted:
        logger.info(f"User {current_user.id} deleted AI config (reset to system default)")
    return {"message": "已恢復使用系統預設 AI 設定"}


@router.post("/test")
@limiter.limit("5/minute")
def test_ai_config(
    request: Request,
    payload: AIConfigTestRequest,
    current_user: User = Depends(get_current_user),
):
    """測試 API Key 是否有效"""
    result = AIClientFactory.test_client(
        provider=payload.provider,
        model=payload.model,
        api_key=payload.api_key,
    )
    return result
