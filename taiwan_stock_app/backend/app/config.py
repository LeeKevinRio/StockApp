"""
Application configuration
"""
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


class Settings:
    """Application settings"""

    # 環境偵測
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    PORT: int = int(os.getenv("PORT", "8000"))
    IS_PRODUCTION: bool = os.getenv("ENVIRONMENT", "development") == "production"

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/taiwan_stock"
    )

    # API Keys
    FINMIND_TOKEN: str = os.getenv("FINMIND_TOKEN", "")
    FUGLE_API_KEY: str = os.getenv("FUGLE_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Model (Google Gemini) - Default model (backward compatibility)
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.5-flash")

    # AI Models by subscription tier
    # Free: 2.5-flash 無 thinking | Pro: 3-flash + thinking 深度推理
    AI_MODEL_FREE: str = os.getenv("AI_MODEL_FREE", "gemini-2.5-flash")
    AI_MODEL_PRO: str = os.getenv("AI_MODEL_PRO", "gemini-3-flash-preview")

    # 開發模式：強制所有用戶使用 Pro 模型（上線前關掉）
    DEV_FORCE_PRO: bool = os.getenv("DEV_FORCE_PRO", "false").lower() == "true"

    # Groq Model (fallback when Gemini quota exceeded)
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # FRED API (宏觀經濟數據)
    FRED_API_KEY: str = os.getenv("FRED_API_KEY", "")

    # CORS — 生產環境加入前端正式域名
    _default_cors = "http://localhost:5000,http://localhost:3000,http://localhost:8080"
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", _default_cors).split(",")


settings = Settings()

# 安全警告：檢查 JWT 密鑰是否為預設值
_DEFAULT_SECRETS = {"your-secret-key-change-in-production", "your_jwt_secret_key_change_in_production", ""}
if settings.IS_PRODUCTION and settings.JWT_SECRET in _DEFAULT_SECRETS:
    raise RuntimeError(
        "生產環境禁止使用預設 JWT_SECRET！請在環境變數中設定安全的隨機密鑰。"
    )
elif settings.JWT_SECRET in _DEFAULT_SECRETS:
    logger.warning(
        "JWT_SECRET 使用預設值，請在 .env 中設定安全的隨機密鑰！"
    )
