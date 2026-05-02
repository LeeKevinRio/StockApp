"""
JWT Secret 持久化 (lazy load + race-safe)

設計目的：
- 解決「後端重啟使用者就被踢出」的根本問題
- 即使 startup hook 失敗（DB 冷啟動、暫時性錯誤），第一個 request 仍會自動載入
- 環境變數 JWT_SECRET > DB system_config > 自動生成寫入 DB

呼叫方式：
    from app.auth_secret import get_jwt_secret
    token = jwt.encode(payload, get_jwt_secret(), algorithm="HS256")
"""
import logging
import os
import secrets as _secrets
import threading

logger = logging.getLogger(__name__)

_DEFAULT_JWT_SECRETS = {
    "your-secret-key-change-in-production",
    "your_jwt_secret_key_change_in_production",
    "",
}

# Module-level cache
_cached_secret: str | None = None
_lock = threading.Lock()
_load_attempted_in_request = False  # 用於避免單一 request 內重複嘗試


def _load_from_db() -> str | None:
    """從 DB system_config 讀取或寫入 secret，回傳最終值；DB 不通則回 None。"""
    try:
        from app.database import SessionLocal
        from app.models import SystemConfig
        from sqlalchemy.exc import IntegrityError
    except Exception as e:
        logger.warning(f"JWT secret: model import failed: {e}")
        return None

    db = SessionLocal()
    try:
        cfg = db.query(SystemConfig).filter(SystemConfig.key == "jwt_secret").first()
        if cfg and cfg.value:
            logger.info("JWT secret loaded from DB")
            return cfg.value

        # 第一次：生成並寫入。Race-safe：若另一 worker 已寫入，回查既有值。
        new_secret = _secrets.token_urlsafe(48)
        try:
            db.add(SystemConfig(key="jwt_secret", value=new_secret))
            db.commit()
            logger.warning("JWT secret generated and stored in DB (will persist)")
            return new_secret
        except IntegrityError:
            # 並行寫入衝突，重查既有值
            db.rollback()
            cfg = db.query(SystemConfig).filter(SystemConfig.key == "jwt_secret").first()
            if cfg and cfg.value:
                logger.info("JWT secret loaded from DB (after race)")
                return cfg.value
            return None
    except Exception as e:
        logger.warning(f"JWT secret DB load failed: {e}")
        return None
    finally:
        try:
            db.close()
        except Exception:
            pass


def get_jwt_secret() -> str:
    """
    取得 JWT secret（lazy load + cache）。

    優先順序：
    1. 已 cache 的值
    2. 環境變數 JWT_SECRET（非預設）
    3. DB system_config.jwt_secret
    4. 生成新值寫入 DB
    5. 全部失敗 → fallback 到 settings.JWT_SECRET（但會 log error，可能會導致登入狀態不穩）
    """
    global _cached_secret

    if _cached_secret:
        return _cached_secret

    with _lock:
        if _cached_secret:
            return _cached_secret

        # 1. 環境變數優先
        env_secret = os.getenv("JWT_SECRET", "")
        if env_secret and env_secret not in _DEFAULT_JWT_SECRETS:
            _cached_secret = env_secret
            logger.info("JWT secret loaded from env")
            return _cached_secret

        # 2. 從 DB 讀/寫
        db_secret = _load_from_db()
        if db_secret:
            _cached_secret = db_secret
            return _cached_secret

        # 3. 最後 fallback：用 settings 當前值（可能是 import 時自動生成的隨機值）
        # 這個情況 token 會在下次重啟失效，但至少這次 request 不會 500
        from app.config import settings
        logger.error(
            "JWT secret could not be persisted to DB — falling back to in-memory secret. "
            "Tokens may not survive restart!"
        )
        _cached_secret = settings.JWT_SECRET
        return _cached_secret


def preload_jwt_secret() -> bool:
    """
    啟動時主動預載入。失敗也沒關係，第一個 request 會自動 lazy load。
    回傳 True/False 方便上層 log。
    """
    try:
        secret = get_jwt_secret()
        return bool(secret) and secret not in _DEFAULT_JWT_SECRETS
    except Exception as e:
        logger.error(f"preload_jwt_secret failed: {e}")
        return False


def reset_cache_for_test():
    """測試專用：重設 cache"""
    global _cached_secret
    with _lock:
        _cached_secret = None
