# core/facebook_auth.py

import os
import urllib.parse
from typing import Optional

try:
    import httpx
    _HAS_HTTPX = True
except ImportError:
    import urllib.request
    import json as _json
    _HAS_HTTPX = False

# Configuration Facebook OAuth
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
FACEBOOK_AUTH_URL = "https://www.facebook.com/v19.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
FACEBOOK_USER_URL = "https://graph.facebook.com/v19.0/me"


class FacebookAuthProvider:
    """Gère l'authentification Facebook OAuth2."""

    def __init__(self, app_id: Optional[str] = None, app_secret: Optional[str] = None):
        self.app_id = app_id or FACEBOOK_APP_ID
        self.app_secret = app_secret or FACEBOOK_APP_SECRET

        if not self.app_id:
            print("⚠️  FACEBOOK_APP_ID non configuré. L'authentification Facebook sera désactivée.")

    def get_auth_url(self, redirect_uri: str) -> str:
        """Génère l'URL d'autorisation Facebook."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": redirect_uri,
            "scope": "email,public_profile",
            "response_type": "code",
        }
        return f"{FACEBOOK_AUTH_URL}?{urllib.parse.urlencode(params)}"

    def verify_facebook_callback(self, code: str, redirect_uri: str) -> Optional[dict]:
        """
        Échange le code d'autorisation contre un token et retourne les infos utilisateur.

        Args:
            code: Code d'autorisation reçu du callback
            redirect_uri: URL de callback (doit correspondre)

        Returns:
            Dictionnaire avec les informations utilisateur ou None si invalide
        """
        if not self.app_id or not self.app_secret:
            raise ValueError("Facebook App ID/Secret non configuré")

        try:
            # Étape 1 : Échanger le code contre un access token
            token_params = {
                "client_id": self.app_id,
                "client_secret": self.app_secret,
                "redirect_uri": redirect_uri,
                "code": code,
            }

            token_data = self._http_get(FACEBOOK_TOKEN_URL, token_params)

            if not token_data or "access_token" not in token_data:
                print(f"❌ Erreur Facebook token: {token_data}")
                return None

            access_token = token_data["access_token"]

            # Étape 2 : Récupérer les infos utilisateur
            user_params = {
                "fields": "id,name,email",
                "access_token": access_token,
            }

            user_data = self._http_get(FACEBOOK_USER_URL, user_params)

            if not user_data or "id" not in user_data:
                print(f"❌ Erreur Facebook user info: {user_data}")
                return None

            email = user_data.get("email")
            if not email:
                print("❌ Pas d'email dans le profil Facebook (permission non accordée ?)")
                return None

            return {
                "facebook_id": user_data["id"],
                "email": email,
                "full_name": user_data.get("name"),
            }

        except Exception as e:
            print(f"❌ Erreur lors de la vérification Facebook: {e}")
            return None

    def _http_get(self, url: str, params: dict) -> Optional[dict]:
        """Effectue une requête GET et retourne le JSON."""
        full_url = f"{url}?{urllib.parse.urlencode(params)}"

        if _HAS_HTTPX:
            with httpx.Client() as client:
                resp = client.get(full_url)
                return resp.json()
        else:
            req = urllib.request.Request(full_url)
            with urllib.request.urlopen(req) as resp:
                return _json.loads(resp.read().decode("utf-8"))

    def is_enabled(self) -> bool:
        """Retourne True si l'authentification Facebook est configurée."""
        return bool(self.app_id and self.app_secret)


# Instance globale
facebook_auth_provider = FacebookAuthProvider()
