# core/google_auth.py

import os
from google.oauth2 import id_token
from google.auth.transport import requests
from typing import Optional

# Configuration Google OAuth
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")


class GoogleAuthProvider:
    """Gère l'authentification Google OpenID Connect."""

    def __init__(self, client_id: Optional[str] = None):
        """
        Initialise le provider Google Auth.

        Args:
            client_id: Client ID Google (optionnel, utilise GOOGLE_CLIENT_ID par défaut)
        """
        self.client_id = client_id or GOOGLE_CLIENT_ID

        if not self.client_id:
            print("⚠️  GOOGLE_CLIENT_ID non configuré. L'authentification Google sera désactivée.")

    def verify_google_token(self, token: str) -> Optional[dict]:
        """
        Vérifie un token Google et retourne les informations utilisateur.

        Args:
            token: Token ID Google

        Returns:
            Dictionnaire avec les informations utilisateur ou None si invalide
        """
        if not self.client_id:
            raise ValueError("Google Client ID non configuré")

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
            # Token invalide
            print(f"❌ Erreur de vérification du token Google: {e}")
            return None
        except Exception as e:
            # Autre erreur
            print(f"❌ Erreur lors de la vérification Google: {e}")
            return None

    def is_enabled(self) -> bool:
        """Retourne True si l'authentification Google est configurée."""
        return bool(self.client_id)


# Instance globale
google_auth_provider = GoogleAuthProvider()
