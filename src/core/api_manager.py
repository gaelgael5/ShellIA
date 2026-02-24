# core/api_manager.py

import json
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class APIManager:
    """
    Gère les configurations des APIs IA (Claude, ChatGPT, etc.).
    """

    def __init__(self, config_file: Optional[Path] = None):
        """
        Initialise le gestionnaire d'APIs.

        Args:
            config_file: Chemin vers le fichier de configuration des APIs
        """
        if config_file is None:
            # Par défaut, le fichier apis.json à la racine du projet
            self.config_file = Path(__file__).parent.parent.parent / "apis.json"
        else:
            self.config_file = Path(config_file)

        self.apis = []
        self._load_config()

    def _load_config(self):
        """Charge la configuration depuis le fichier JSON."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.apis = data.get('apis', [])
                    logger.info(f"{len(self.apis)} API(s) chargée(s)")
            except Exception as e:
                logger.error(f"Erreur lors du chargement des APIs: {e}")
                self.apis = []
        else:
            # Créer un fichier vide avec une structure par défaut
            self.apis = []
            self._save_config()

    def _save_config(self):
        """Sauvegarde la configuration dans le fichier JSON."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump({'apis': self.apis}, f, indent=2, ensure_ascii=False)
            logger.info("Configuration des APIs sauvegardée")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}")
            return False

    def list_apis(self) -> List[Dict]:
        """
        Liste toutes les APIs configurées.

        Returns:
            Liste de dictionnaires avec les infos de chaque API
        """
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
        """
        Récupère les détails d'une API.

        Args:
            api_id: ID de l'API

        Returns:
            Dictionnaire avec toutes les informations de l'API
        """
        for api in self.apis:
            if api["id"] == api_id:
                return api.copy()
        return None

    def create_api(self, api_data: Dict) -> bool:
        """
        Crée une nouvelle configuration API.

        Args:
            api_data: Dictionnaire avec les données de l'API

        Returns:
            True si créé avec succès, False sinon
        """
        # Vérifier que l'ID n'existe pas déjà
        if any(api["id"] == api_data["id"] for api in self.apis):
            logger.warning(f"L'API {api_data['id']} existe déjà")
            return False

        self.apis.append(api_data)
        return self._save_config()

    def update_api(self, api_id: str, api_data: Dict) -> bool:
        """
        Met à jour une API existante.

        Args:
            api_id: ID de l'API
            api_data: Nouvelles données

        Returns:
            True si mis à jour avec succès, False sinon
        """
        for i, api in enumerate(self.apis):
            if api["id"] == api_id:
                # Conserver l'ID même si modifié dans api_data
                api_data["id"] = api_id
                self.apis[i] = api_data
                return self._save_config()

        logger.warning(f"L'API {api_id} n'existe pas")
        return False

    def delete_api(self, api_id: str) -> bool:
        """
        Supprime une API.

        Args:
            api_id: ID de l'API

        Returns:
            True si supprimé avec succès, False sinon
        """
        initial_len = len(self.apis)
        self.apis = [api for api in self.apis if api["id"] != api_id]

        if len(self.apis) < initial_len:
            return self._save_config()
        else:
            logger.warning(f"L'API {api_id} n'existe pas")
            return False


# Instance singleton globale
_api_manager = APIManager()


def get_api_manager() -> APIManager:
    """Retourne l'instance globale du gestionnaire d'APIs."""
    return _api_manager
