"""
Application configuration
"""
import os
from typing import Optional


class Settings:
    """Application settings"""

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://user:password@localhost:5432/taiwan_stock"
    )

    # API Keys
    FINMIND_TOKEN: str = os.getenv("FINMIND_TOKEN", "")
    FUGLE_API_KEY: str = os.getenv("FUGLE_API_KEY", "")
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Model (Google Gemini)
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-1.5-flash")

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]


settings = Settings()
