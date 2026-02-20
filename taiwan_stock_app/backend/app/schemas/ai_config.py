"""
AI Config Schemas — BYOK 設定的請求/回應模型
"""

from pydantic import BaseModel, field_validator
from typing import List, Optional


# 可用的 provider + model 清單
AI_PROVIDERS = {
    "gemini": {
        "label": "Google Gemini",
        "models": ["gemini-2.0-flash", "gemini-2.5-pro"],
    },
    "openai": {
        "label": "OpenAI",
        "models": ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1"],
    },
    "groq": {
        "label": "Groq",
        "models": ["llama-3.3-70b-versatile", "llama-4-maverick-17b-128e"],
    },
}

VALID_PROVIDERS = set(AI_PROVIDERS.keys())
VALID_MODELS = {m for p in AI_PROVIDERS.values() for m in p["models"]}


class AIModelInfo(BaseModel):
    id: str
    label: str


class AIProviderInfo(BaseModel):
    id: str
    label: str
    models: List[AIModelInfo]


class AIProvidersResponse(BaseModel):
    providers: List[AIProviderInfo]


class AIConfigSave(BaseModel):
    provider: str
    model: str
    api_key: str

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_PROVIDERS:
            raise ValueError(f"不支援的 provider: {v}，可選: {', '.join(VALID_PROVIDERS)}")
        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        v = v.strip()
        if v not in VALID_MODELS:
            raise ValueError(f"不支援的 model: {v}")
        return v

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 10:
            raise ValueError("API Key 長度不足")
        return v


class AIConfigResponse(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    has_api_key: bool = False
    provider_label: Optional[str] = None


class AIConfigTestRequest(BaseModel):
    provider: str
    model: str
    api_key: str

    @field_validator("provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        v = v.lower().strip()
        if v not in VALID_PROVIDERS:
            raise ValueError(f"不支援的 provider: {v}")
        return v
