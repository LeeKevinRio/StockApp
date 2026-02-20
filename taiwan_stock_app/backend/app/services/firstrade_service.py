"""
Firstrade 券商服務 — 帳戶連結、2FA 驗證、持倉同步
"""

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.broker import BrokerAccount, BrokerPosition
from app.services.crypto_service import encrypt_credentials, decrypt_credentials

logger = logging.getLogger(__name__)


class FirstradeService:
    """Firstrade 帳戶連動服務"""

    def link_account(self, db: Session, user_id: int, username: str, password: str, pin: str) -> dict:
        """
        連結 Firstrade 帳戶：嘗試登入，若需 2FA 則回傳 pending 狀態
        """
        # 檢查是否已連結
        existing = db.query(BrokerAccount).filter(
            BrokerAccount.user_id == user_id,
            BrokerAccount.broker_type == "firstrade",
        ).first()
        if existing and existing.status == "active":
            return {
                "account_id": existing.id,
                "status": "active",
                "message": "帳戶已連結",
            }

        try:
            from firstrade import account as ft_account
            from firstrade.account import FTSession

            # 嘗試登入
            ft_session = FTSession(username=username, password=password, pin=pin)

            if ft_session.need_code:
                # 需要 2FA — 儲存帳密（加密），等待驗證碼
                creds = encrypt_credentials({
                    "username": username,
                    "password": password,
                    "pin": pin,
                })
                if existing:
                    existing.encrypted_credentials = creds
                    existing.status = "pending_2fa"
                else:
                    existing = BrokerAccount(
                        user_id=user_id,
                        broker_type="firstrade",
                        encrypted_credentials=creds,
                        status="pending_2fa",
                    )
                    db.add(existing)
                db.commit()
                db.refresh(existing)
                return {
                    "account_id": existing.id,
                    "status": "needs_2fa",
                    "message": "請輸入 2FA 驗證碼",
                }

            # 登入成功，儲存 session tokens
            return self._save_active_session(db, user_id, existing, ft_session, username)

        except Exception as e:
            logger.error(f"Firstrade 登入失敗: {e}")
            if existing:
                existing.status = "error"
                db.commit()
            return {
                "account_id": existing.id if existing else 0,
                "status": "error",
                "message": "連結失敗，請檢查帳號密碼",
            }

    def verify_2fa(self, db: Session, user_id: int, account_id: int, code: str) -> dict:
        """驗證 2FA 碼並完成連結"""
        account = db.query(BrokerAccount).filter(
            BrokerAccount.id == account_id,
            BrokerAccount.user_id == user_id,
        ).first()
        if not account:
            return {"account_id": account_id, "status": "error", "message": "帳戶不存在"}
        if account.status != "pending_2fa":
            return {"account_id": account_id, "status": "error", "message": "帳戶不在 2FA 驗證狀態"}

        try:
            creds = decrypt_credentials(account.encrypted_credentials)
            from firstrade import account as ft_account
            from firstrade.account import FTSession

            ft_session = FTSession(
                username=creds["username"],
                password=creds["password"],
                pin=creds["pin"],
                code=code,
            )

            if ft_session.need_code:
                return {
                    "account_id": account_id,
                    "status": "needs_2fa",
                    "message": "驗證碼錯誤，請重試",
                }

            return self._save_active_session(db, user_id, account, ft_session, creds["username"])

        except Exception as e:
            logger.error(f"Firstrade 2FA 驗證失敗: {e}")
            return {"account_id": account_id, "status": "error", "message": "2FA 驗證失敗"}

    def sync_positions(self, db: Session, user_id: int) -> dict:
        """同步 Firstrade 持倉到本地 DB"""
        account = self._get_active_account(db, user_id)
        if not account:
            return {"synced": False, "message": "無已連結帳戶"}

        try:
            ft_session = self._build_session(account)
            if not ft_session:
                account.status = "error"
                db.commit()
                return {"synced": False, "message": "Session 已過期，請重新連結"}

            from firstrade import account as ft_account
            positions_data = ft_account.FTAccountData(ft_session).stock_positions

            # 清除舊持倉
            db.query(BrokerPosition).filter(
                BrokerPosition.broker_account_id == account.id,
            ).delete()

            # 寫入新持倉
            count = 0
            for symbol, pos in positions_data.items():
                quantity = float(pos.get("quantity", 0))
                if quantity == 0:
                    continue
                bp = BrokerPosition(
                    broker_account_id=account.id,
                    symbol=symbol,
                    quantity=quantity,
                    avg_cost=float(pos.get("price_paid", 0)),
                    market_value=float(pos.get("market_value", 0)),
                    unrealized_pnl=float(pos.get("unrealized_gain_loss", 0)),
                    last_updated=datetime.utcnow(),
                )
                db.add(bp)
                count += 1

            account.last_synced = datetime.utcnow()
            # 更新 session tokens
            self._persist_tokens(db, account, ft_session)
            db.commit()

            return {"synced": True, "message": f"已同步 {count} 筆持倉", "count": count}

        except Exception as e:
            logger.error(f"Firstrade 同步持倉失敗: {e}")
            return {"synced": False, "message": "同步失敗，請稍後再試"}

    def get_positions(self, db: Session, user_id: int) -> list:
        """從本地 DB 讀取持倉"""
        account = self._get_active_account(db, user_id)
        if not account:
            return []
        return db.query(BrokerPosition).filter(
            BrokerPosition.broker_account_id == account.id,
        ).all()

    def get_status(self, db: Session, user_id: int) -> dict:
        """取得連結狀態"""
        account = db.query(BrokerAccount).filter(
            BrokerAccount.user_id == user_id,
            BrokerAccount.broker_type == "firstrade",
        ).first()
        if not account or account.status == "error":
            return {"linked": False}
        return {
            "linked": account.status == "active",
            "broker_type": account.broker_type,
            "status": account.status,
            "account_number": account.account_number,
            "last_synced": account.last_synced,
        }

    def unlink(self, db: Session, user_id: int) -> dict:
        """解除連結並清除所有資料"""
        account = db.query(BrokerAccount).filter(
            BrokerAccount.user_id == user_id,
            BrokerAccount.broker_type == "firstrade",
        ).first()
        if not account:
            return {"success": False, "message": "無已連結帳戶"}

        # 刪除持倉
        db.query(BrokerPosition).filter(
            BrokerPosition.broker_account_id == account.id,
        ).delete()
        # 刪除帳戶
        db.delete(account)
        db.commit()
        return {"success": True, "message": "已解除連結"}

    # ==================== 內部方法 ====================

    def _get_active_account(self, db: Session, user_id: int) -> Optional[BrokerAccount]:
        return db.query(BrokerAccount).filter(
            BrokerAccount.user_id == user_id,
            BrokerAccount.broker_type == "firstrade",
            BrokerAccount.status == "active",
        ).first()

    def _save_active_session(self, db: Session, user_id: int,
                             account: Optional[BrokerAccount],
                             ft_session, username: str) -> dict:
        """登入成功後儲存 session"""
        tokens = self._get_tokens(ft_session)
        creds = encrypt_credentials({
            "username": username,
            "session_tokens": tokens,
        })

        account_number = ""
        try:
            from firstrade import account as ft_account
            acct_data = ft_account.FTAccountData(ft_session)
            account_number = acct_data.account_numbers[0] if acct_data.account_numbers else ""
        except Exception:
            pass

        if account:
            account.encrypted_credentials = creds
            account.status = "active"
            account.account_number = account_number
        else:
            account = BrokerAccount(
                user_id=user_id,
                broker_type="firstrade",
                encrypted_credentials=creds,
                status="active",
                account_number=account_number,
            )
            db.add(account)

        db.commit()
        db.refresh(account)
        return {
            "account_id": account.id,
            "status": "active",
            "message": "帳戶連結成功",
        }

    def _get_tokens(self, ft_session) -> dict:
        """從 FTSession 取得可持久化的 tokens"""
        return {
            "cookies": {k: v for k, v in ft_session.session.cookies.get_dict().items()},
            "headers": dict(ft_session.session.headers),
        }

    def _persist_tokens(self, db: Session, account: BrokerAccount, ft_session) -> None:
        """更新帳戶中的 session tokens"""
        try:
            old_creds = decrypt_credentials(account.encrypted_credentials)
            old_creds["session_tokens"] = self._get_tokens(ft_session)
            account.encrypted_credentials = encrypt_credentials(old_creds)
        except Exception as e:
            logger.warning(f"更新 session tokens 失敗: {e}")

    def _build_session(self, account: BrokerAccount):
        """從儲存的 tokens 重建 FTSession"""
        try:
            creds = decrypt_credentials(account.encrypted_credentials)
            tokens = creds.get("session_tokens")
            if not tokens:
                return None

            from firstrade.account import FTSession
            import requests

            session = requests.Session()
            session.cookies.update(tokens.get("cookies", {}))
            session.headers.update(tokens.get("headers", {}))

            ft_session = FTSession.__new__(FTSession)
            ft_session.session = session
            ft_session.need_code = False
            return ft_session
        except Exception as e:
            logger.error(f"重建 Firstrade session 失敗: {e}")
            return None


firstrade_service = FirstradeService()
