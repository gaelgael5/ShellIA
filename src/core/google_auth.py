# core/google_auth.py

import os
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Optional

# Configuration Google OAuth
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")


class GoogleAuthProvider:
    """Manages Google OpenID Connect authentication."""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        """
        Initialise the Google Auth provider.

        Args:
            client_id:     Google OAuth Client ID     (defaults to GOOGLE_CLIENT_ID env var)
            client_secret: Google OAuth Client Secret (defaults to GOOGLE_CLIENT_SECRET env var)
        """
        self.client_id     = client_id     or GOOGLE_CLIENT_ID
        self.client_secret = client_secret or GOOGLE_CLIENT_SECRET

        if not self.client_id:
            print("⚠️  GOOGLE_CLIENT_ID not configured. Google authentication will be disabled.")

    def verify_google_token(self, token: str) -> Optional[dict]:
        """
        Verify a Google ID token and return user information.

        Args:
            token: Google ID token (from the Sign-In button callback)

        Returns:
            Dict with user info, or None if the token is invalid.
        """
        if not self.client_id:
            raise ValueError("Google Client ID is not configured")

        try:
            # Vérifier le token (tolérance de 10s pour les décalages d'horloge)
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                self.client_id,
                clock_skew_in_seconds=10
            )

            # Vérifier que le token est bien pour notre application
            if idinfo['aud'] != self.client_id:
                raise ValueError("Token invalide: audience incorrecte")

            # Retourner les informations utilisateur
            return {
                "google_id": idinfo["sub"],
                "email": idinfo.get("email"),
                "email_verified": idinfo.get("email_verified", False),
                "full_name": idinfo.get("name"),
                "picture": idinfo.get("picture")
            }

        except ValueError as e:
            print(f"❌ Google token verification failed: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during Google verification: {e}")
            return None

    def is_enabled(self) -> bool:
        """Returns True if Google authentication is configured (client ID set)."""
        return bool(self.client_id)


# Global instance — reads GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from environment
google_auth_provider = GoogleAuthProvider()
