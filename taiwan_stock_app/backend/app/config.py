"""
Application configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


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
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # AI Model (Google Gemini) - Default model (backward compatibility)
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-1.5-flash")

    # AI Models by subscription tier
    AI_MODEL_FREE: str = os.getenv("AI_MODEL_FREE", "gemini-2.0-flash")
    AI_MODEL_PRO: str = os.getenv("AI_MODEL_PRO", "gemini-2.5-pro")

    # Groq Model (fallback when Gemini quota exceeded)
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8080"]


settings = Settings()
