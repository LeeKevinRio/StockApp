"""
OAuth Service - Google OAuth 驗證服務
"""
from typing import Optional, Dict
from google.oauth2 import id_token
from google.auth.transport import requests

from app.config import settings


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
            print(f"Verifying Google token with client_id: {settings.GOOGLE_CLIENT_ID[:20]}...")
            print(f"Token preview: {token[:50]}...")

            # Verify the token with Google
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            print(f"Token verified successfully. User: {idinfo.get('email')}")

            # Check issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                print(f"Invalid issuer: {idinfo['iss']}")
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
            print(f"Google token verification failed (ValueError): {e}")
            return None
        except Exception as e:
            print(f"Unexpected error during Google token verification: {type(e).__name__}: {e}")
            return None


oauth_service = OAuthService()
