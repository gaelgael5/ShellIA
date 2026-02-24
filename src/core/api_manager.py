# core/api_manager.py

import json
import os
import base64
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    import hashlib
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logger.warning("cryptography not installed — API keys stored in plain text. Run: pip install cryptography")


def _get_fernet():
    """Create a Fernet instance derived from SECRET_KEY."""
    if not ENCRYPTION_AVAILABLE:
        return None
    secret = os.getenv("SECRET_KEY", "")
    if not secret:
        return None
    # Derive a 32-byte key from SECRET_KEY using SHA-256
    key = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


class APIManager:
    """
    Manages AI API configurations (Claude, ChatGPT, etc.).
    API keys are encrypted at rest using Fernet symmetric encryption.
    """

    def __init__(self, config_file: Optional[Path] = None):
        if config_file is None:
            self.config_file = Path(__file__).parent.parent.parent / "apis.json"
        else:
            self.config_file = Path(config_file)

        self.apis = []
        self._load_config()

    def _encrypt_key(self, value: str) -> str:
        """Encrypt a value if cryptography is available."""
        f = _get_fernet()
        if f and value:
            try:
                return "enc:" + f.encrypt(value.encode()).decode()
            except Exception:
                pass
        return value

    def _decrypt_key(self, value: str) -> str:
        """Decrypt a value if it was encrypted."""
        if not value or not value.startswith("enc:"):
            return value
        f = _get_fernet()
        if f:
            try:
                return f.decrypt(value[4:].encode()).decode()
            except Exception:
                logger.warning("Failed to decrypt API key — key may have been encrypted with a different SECRET_KEY")
                return ""
        return ""

    def _load_config(self):
        """Load configuration from JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.apis = data.get('apis', [])
                    logger.info(f"{len(self.apis)} API(s) loaded")
            except Exception as e:
                logger.error(f"Error loading APIs: {e}")
                self.apis = []
        else:
            self.apis = []
            self._save_config()

    def _save_config(self):
        """Save configuration to JSON file (keys are encrypted)."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'apis': self.apis}, f, indent=2, ensure_ascii=False)
            logger.info("API configuration saved")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def list_apis(self) -> List[Dict]:
        """List all configured APIs (without exposing keys)."""
        return [
            {
                "id": api["id"],
                "name": api["name"],
                "provider": api["provider"],
                "model": api.get("model", "")
            }
            for api in self.apis
        ]

    def get_api(self, api_id: str) -> Optional[Dict]:
        """Get API details including decrypted key."""
        for api in self.apis:
            if api["id"] == api_id:
                result = api.copy()
                # Decrypt the API key before returning
                if "api_key" in result:
                    result["api_key"] = self._decrypt_key(result["api_key"])
                return result
        return None

    def create_api(self, api_data: Dict) -> bool:
        """Create a new API configuration (encrypts the key)."""
        if any(api["id"] == api_data.get("id") for api in self.apis):
            logger.warning(f"API {api_data.get('id')} already exists")
            return False
        # Encrypt API key before storing
        if "api_key" in api_data and api_data["api_key"]:
            api_data = api_data.copy()
            api_data["api_key"] = self._encrypt_key(api_data["api_key"])
        self.apis.append(api_data)
        return self._save_config()

    def update_api(self, api_id: str, api_data: Dict) -> bool:
        """Update an existing API configuration."""
        for i, api in enumerate(self.apis):
            if api["id"] == api_id:
                updated = {**api, **api_data, "id": api_id}
                # Re-encrypt if key changed
                if "api_key" in api_data and api_data["api_key"]:
                    updated["api_key"] = self._encrypt_key(api_data["api_key"])
                self.apis[i] = updated
                return self._save_config()
        return False

    def delete_api(self, api_id: str) -> bool:
        """Delete an API configuration."""
        original_count = len(self.apis)
        self.apis = [api for api in self.apis if api["id"] != api_id]
        if len(self.apis) < original_count:
            return self._save_config()
        return False


# Global singleton instance
_api_manager = APIManager()


def get_api_manager() -> APIManager:
    """Return the global APIManager instance."""
    return _api_manager
