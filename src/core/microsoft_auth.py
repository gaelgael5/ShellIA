# core/microsoft_auth.py

import os
from typing import Optional
import msal

# Configuration Microsoft OAuth
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID", "")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET", "")
MICROSOFT_AUTHORITY = "https://login.microsoftonline.com/common"
MICROSOFT_SCOPES = ["User.Read"]


class MicrosoftAuthProvider:
    """Gère l'authentification Microsoft OpenID Connect."""

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self.client_id = client_id or MICROSOFT_CLIENT_ID
        self.client_secret = client_secret or MICROSOFT_CLIENT_SECRET

        if not self.client_id:
            print("⚠️  MICROSOFT_CLIENT_ID non configuré. L'authentification Microsoft sera désactivée.")

        self._app = None

    def _get_msal_app(self) -> msal.ConfidentialClientApplication:
        """Retourne l'application MSAL (lazy init)."""
        if self._app is None:
            self._app = msal.ConfidentialClientApplication(
                self.client_id,
                authority=MICROSOFT_AUTHORITY,
                client_credential=self.client_secret,
            )
        return self._app

    def get_auth_url(self, redirect_uri: str) -> str:
        """
        Génère l'URL d'autorisation Microsoft.

        Args:
            redirect_uri: URL de callback après authentification

        Returns:
            URL vers laquelle rediriger l'utilisateur
        """
        app = self._get_msal_app()
        flow = app.initiate_auth_code_flow(
            scopes=MICROSOFT_SCOPES,
            redirect_uri=redirect_uri,
        )
        # Stocker le flow pour la vérification du callback
        self._current_flow = flow
        return flow["auth_uri"]

    def verify_microsoft_callback(self, query_params: dict, redirect_uri: str) -> Optional[dict]:
        """
        Échange le code d'autorisation contre un token et retourne les infos utilisateur.

        Args:
            query_params: Paramètres de la requête callback (contient le code)
            redirect_uri: URL de callback (doit correspondre à celle utilisée pour get_auth_url)

        Returns:
            Dictionnaire avec les informations utilisateur ou None si invalide
        """
        if not self.client_id:
            raise ValueError("Microsoft Client ID non configuré")

        try:
            app = self._get_msal_app()

            # Si on n'a pas de flow en cours, en créer un pour le callback
            if not hasattr(self, '_current_flow') or not self._current_flow:
                # Fallback : acquérir le token directement avec le code
                result = app.acquire_token_by_authorization_code(
                    code=query_params.get("code", ""),
                    scopes=MICROSOFT_SCOPES,
                    redirect_uri=redirect_uri,
                )
            else:
                result = app.acquire_token_by_auth_code_flow(
                    self._current_flow,
                    query_params,
                )
                self._current_flow = None

            if "error" in result:
                print(f"❌ Erreur Microsoft Auth: {result.get('error_description', result.get('error'))}")
                return None

            # Extraire les infos utilisateur du token ID
            id_token_claims = result.get("id_token_claims", {})

            if not id_token_claims:
                print("❌ Pas de claims dans le token Microsoft")
                return None

            email = id_token_claims.get("preferred_username") or id_token_claims.get("email")
            if not email:
                print("❌ Pas d'email dans le token Microsoft")
                return None

            return {
                "microsoft_id": id_token_claims.get("oid") or id_token_claims.get("sub"),
                "email": email,
                "full_name": id_token_claims.get("name"),
            }

        except Exception as e:
            print(f"❌ Erreur lors de la vérification Microsoft: {e}")
            return None

    def is_enabled(self) -> bool:
        """Retourne True si l'authentification Microsoft est configurée."""
        return bool(self.client_id and self.client_secret)


# Instance globale
microsoft_auth_provider = MicrosoftAuthProvider()
