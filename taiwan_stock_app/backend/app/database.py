"""
Database configuration and session management
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import logging

logger = logging.getLogger(__name__)

# 確保 .env 在讀取環境變數前載入
_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_backend_dir, ".env"))

_raw_url = os.getenv("DATABASE_URL", "sqlite:///./taiwan_stock.db")

# Railway 給 postgres://，SQLAlchemy 2.x 要求 postgresql://
if _raw_url.startswith("postgres://"):
    _raw_url = _raw_url.replace("postgres://", "postgresql://", 1)

if _raw_url.startswith("sqlite:///./"):
    _db_filename = _raw_url.replace("sqlite:///./", "")
    DATABASE_URL = f"sqlite:///{os.path.join(_backend_dir, _db_filename)}"
else:
    DATABASE_URL = _raw_url

# 根據資料庫類型設定引擎參數
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL 連線池設定（適用於生產環境）
    engine = create_engine(
        DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in database"""
    Base.metadata.create_all(bind=engine)
    _run_migrations()


def _run_migrations():
    """執行資料庫遷移：為已存在的表新增缺少的欄位"""
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    with engine.connect() as conn:
        # 遷移 1: watchlist 表新增 group_id 欄位
        if 'watchlist' in table_names:
            columns = [c['name'] for c in inspector.get_columns('watchlist')]
            if 'group_id' not in columns:
                logger.info("Migration: Adding group_id column to watchlist table")
                conn.execute(text(
                    "ALTER TABLE watchlist ADD COLUMN group_id INTEGER "
                    "REFERENCES watchlist_groups(id) ON DELETE SET NULL"
                ))
                conn.commit()

        # 遷移 2: ai_reports 表新增缺少的欄位
        if 'ai_reports' in table_names:
            columns = [c['name'] for c in inspector.get_columns('ai_reports')]
            new_columns = {
                'current_price': 'NUMERIC(10, 2)',
                'entry_price_min': 'NUMERIC(10, 2)',
                'entry_price_max': 'NUMERIC(10, 2)',
                'take_profit_targets': 'TEXT',
                'risk_level': 'VARCHAR(20)',
                'time_horizon': 'VARCHAR(50)',
                'predicted_change_percent': 'NUMERIC(5, 2)',
                'next_day_prediction': 'TEXT',
            }
            for col_name, col_type in new_columns.items():
                if col_name not in columns:
                    logger.info(f"Migration: Adding {col_name} column to ai_reports table")
                    conn.execute(text(
                        f"ALTER TABLE ai_reports ADD COLUMN {col_name} {col_type}"
                    ))
            conn.commit()

        logger.info("Database migrations completed")
