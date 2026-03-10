"""
Application configuration
"""
import os
import logging
import secrets
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

    # 登入白名單（正式開放前僅允許指定 Google 帳號）
    # 設為空字串則不限制
    ALLOWED_EMAILS: list = [
        e.strip() for e in os.getenv("ALLOWED_EMAILS", "kavinleejn@gmail.com").split(",") if e.strip()
    ]

    # CORS — 生產環境加入雲端域名（Web 前端部署時需要）
    _default_cors = "http://localhost:5000,http://localhost:3000,http://localhost:8080,https://stockapp-production-0b90.up.railway.app,https://stockapp-backend-ein8.onrender.com,https://leekevinrio.github.io"
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", _default_cors).split(",")


settings = Settings()

# 安全警告：檢查 JWT 密鑰是否為預設值
_DEFAULT_SECRETS = {"your-secret-key-change-in-production", "your_jwt_secret_key_change_in_production", ""}
if settings.IS_PRODUCTION and settings.JWT_SECRET in _DEFAULT_SECRETS:
    # 生產環境缺少 JWT_SECRET：自動生成隨機密鑰（重啟後失效，用戶需重新登入）
    _auto_secret = secrets.token_urlsafe(48)
    settings.JWT_SECRET = _auto_secret
    logger.critical(
        "⚠️ 生產環境未設定 JWT_SECRET，已自動生成臨時密鑰（重啟後失效）。"
        "請在 Railway 環境變數中設定永久的 JWT_SECRET！"
    )
elif settings.JWT_SECRET in _DEFAULT_SECRETS:
    logger.warning(
        "JWT_SECRET 使用預設值，請在 .env 中設定安全的隨機密鑰！"
    )
