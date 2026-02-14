"""
Database configuration and session management
"""
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./taiwan_stock.db"
)

# SQLite 需要特殊的連接參數
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

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

    with engine.connect() as conn:
        # 遷移 1: watchlist 表新增 group_id 欄位
        if 'watchlist' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('watchlist')]
            if 'group_id' not in columns:
                logger.info("Migration: Adding group_id column to watchlist table")
                conn.execute(text(
                    "ALTER TABLE watchlist ADD COLUMN group_id INTEGER "
                    "REFERENCES watchlist_groups(id) ON DELETE SET NULL"
                ))
                conn.commit()

        logger.info("Database migrations completed")
