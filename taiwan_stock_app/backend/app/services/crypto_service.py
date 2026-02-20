"""
加密服務 — 使用 Fernet 對稱加密保護券商憑證
"""

import json
import logging
import os

from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)

_ENCRYPTION_KEY = os.getenv("BROKER_ENCRYPTION_KEY")


def _get_fernet() -> Fernet:
    """取得 Fernet 實例，金鑰由環境變數提供"""
    if not _ENCRYPTION_KEY:
        raise RuntimeError("BROKER_ENCRYPTION_KEY 環境變數未設定")
    return Fernet(_ENCRYPTION_KEY.encode())


def encrypt_credentials(data: dict) -> str:
    """將憑證 dict 加密為字串"""
    f = _get_fernet()
    plaintext = json.dumps(data).encode()
    return f.encrypt(plaintext).decode()


def decrypt_credentials(token: str) -> dict:
    """將加密字串解密回 dict"""
    f = _get_fernet()
    try:
        plaintext = f.decrypt(token.encode())
        return json.loads(plaintext.decode())
    except InvalidToken:
        logger.error("憑證解密失敗：金鑰不匹配或資料損壞")
        raise ValueError("無法解密憑證")


def generate_key() -> str:
    """產生新的 Fernet 金鑰（用於初始設定）"""
    return Fernet.generate_key().decode()
