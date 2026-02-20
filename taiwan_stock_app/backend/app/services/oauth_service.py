"""
OAuth Service - Google OAuth 驗證服務
"""
from typing import Optional, Dict
from google.oauth2 import id_token
from google.auth.transport import requests
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class OAuthService:
    """OAuth 驗證服務"""

    @staticmethod
    def verify_google_token(token: str) -> Optional[Dict]:
        """
        驗證 Google ID token 並返回用戶資訊

        Args:
            token: Google ID token

        Returns:
            用戶資訊字典，包含 google_id, email, name, picture
            如果驗證失敗返回 None
        """
        try:
            logger.info("Verifying Google token...")

            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            logger.info("Token verified successfully for user: %s", idinfo.get('email'))

            # Check issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.warning("Invalid issuer: %s", idinfo['iss'])
                return None

            # Extract user info
            return {
                'google_id': idinfo['sub'],
                'email': idinfo['email'],
                'name': idinfo.get('name', ''),
                'picture': idinfo.get('picture', ''),
                'email_verified': idinfo.get('email_verified', False)
            }

        except ValueError as e:
            # Invalid token
            logger.warning("Google token verification failed (ValueError): %s", e)
            return None
        except Exception as e:
            logger.error("Unexpected error during Google token verification: %s: %s", type(e).__name__, e)
            return None


oauth_service = OAuthService()
