# core/environment_manager.py

import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class EnvironmentManager:
    """
    Gère les fichiers d'environnement (.env) du projet.
    """

    def __init__(self, environments_dir: Optional[Path] = None):
        """
        Initialise le gestionnaire d'environnements.

        Args:
            environments_dir: Chemin vers le dossier des environnements
        """
        if environments_dir is None:
            # Par défaut, le dossier environments à la racine du projet
            self.environments_dir = Path(__file__).parent.parent.parent / "environments"
        else:
            self.environments_dir = Path(environments_dir)

        # Créer le dossier s'il n'existe pas
        self.environments_dir.mkdir(parents=True, exist_ok=True)

        self.current_env = None
        self.current_env_data = {}

    def list_environments(self) -> List[Dict[str, str]]:
        """
        Liste tous les environnements disponibles.

        Returns:
            Liste de dictionnaires avec les infos de chaque environnement
        """
        environments = []

        for env_file in self.environments_dir.glob("*.env"):
            # Ignorer template.env et .env.example
            if env_file.name in ["template.env", ".env.example"]:
                continue

            env_name = env_file.stem
            env_data = self._parse_env_file(env_file)

            environments.append({
                "filename": env_name,
                "display_name": env_data.get("ENV_NAME", env_name),
                "description": env_data.get("ENV_DESCRIPTION", ""),
                "execution_mode": env_data.get("EXECUTION_MODE", "local"),
                "ai_provider": env_data.get("AI_PROVIDER", "claude"),
                "is_active": env_name == self.current_env
            })

        return sorted(environments, key=lambda x: x["filename"])

    def get_environment(self, env_name: str) -> Optional[Dict[str, str]]:
        """
        Récupère les détails d'un environnement.

        Args:
            env_name: Nom de l'environnement (sans .env)

        Returns:
            Dictionnaire avec toutes les variables d'environnement
        """
        env_file = self.environments_dir / f"{env_name}.env"

        if not env_file.exists():
            return None

        return self._parse_env_file(env_file)

    def create_environment(self, env_name: str, env_data: Dict[str, str]) -> bool:
        """
        Crée un nouvel environnement.

        Args:
            env_name: Nom de l'environnement
            env_data: Dictionnaire des variables d'environnement

        Returns:
            True si créé avec succès, False sinon
        """
        env_file = self.environments_dir / f"{env_name}.env"

        # Ne pas écraser un fichier existant
        if env_file.exists():
            logger.warning(f"L'environnement {env_name} existe déjà")
            return False

        return self._write_env_file(env_file, env_data)

    def update_environment(self, env_name: str, env_data: Dict[str, str]) -> bool:
        """
        Met à jour un environnement existant.

        Args:
            env_name: Nom de l'environnement
            env_data: Dictionnaire des variables d'environnement

        Returns:
            True si mis à jour avec succès, False sinon
        """
        env_file = self.environments_dir / f"{env_name}.env"

        if not env_file.exists():
            logger.warning(f"L'environnement {env_name} n'existe pas")
            return False

        return self._write_env_file(env_file, env_data)

    def delete_environment(self, env_name: str) -> bool:
        """
        Supprime un environnement.

        Args:
            env_name: Nom de l'environnement

        Returns:
            True si supprimé avec succès, False sinon
        """
        env_file = self.environments_dir / f"{env_name}.env"

        if not env_file.exists():
            logger.warning(f"L'environnement {env_name} n'existe pas")
            return False

        # Ne pas supprimer l'environnement actif
        if env_name == self.current_env:
            logger.warning(f"Impossible de supprimer l'environnement actif")
            return False

        try:
            env_file.unlink()
            logger.info(f"Environnement {env_name} supprimé")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return False

    def load_environment(self, env_name: str) -> bool:
        """
        Charge un environnement (met à jour les variables d'environnement).

        Args:
            env_name: Nom de l'environnement

        Returns:
            True si chargé avec succès, False sinon
        """
        env_data = self.get_environment(env_name)

        if env_data is None:
            logger.warning(f"L'environnement {env_name} n'existe pas")
            return False

        # Mettre à jour les variables d'environnement
        for key, value in env_data.items():
            os.environ[key] = value

        self.current_env = env_name
        self.current_env_data = env_data

        logger.info(f"Environnement {env_name} chargé")
        return True

    def _parse_env_file(self, env_file: Path) -> Dict[str, str]:
        """
        Parse un fichier .env et retourne un dictionnaire.

        Args:
            env_file: Chemin vers le fichier .env

        Returns:
            Dictionnaire des variables d'environnement
        """
        env_data = {}

        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()

                    # Ignorer les commentaires et lignes vides
                    if not line or line.startswith('#'):
                        continue

                    # Parse KEY=VALUE
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Retirer les guillemets si présents
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]
                        elif value.startswith("'") and value.endswith("'"):
                            value = value[1:-1]

                        env_data[key] = value

        except Exception as e:
            logger.error(f"Erreur lors de la lecture de {env_file}: {e}")

        return env_data

    def _write_env_file(self, env_file: Path, env_data: Dict[str, str]) -> bool:
        """
        Écrit un fichier .env à partir d'un dictionnaire.

        Args:
            env_file: Chemin vers le fichier .env
            env_data: Dictionnaire des variables d'environnement

        Returns:
            True si écrit avec succès, False sinon
        """
        try:
            with open(env_file, 'w', encoding='utf-8') as f:
                f.write("# ShellIA - Configuration Environment Variables\n")
                f.write("# Généré automatiquement\n\n")

                # Sections définies
                sections = {
                    "ENVIRONMENT IDENTIFICATION": ["ENV_NAME", "ENV_DESCRIPTION"],
                    "API CONFIGURATION": ["AI_API_ID"],
                    "AI PROVIDER SELECTION": ["AI_PROVIDER"],
                    "CLAUDE (ANTHROPIC) CONFIGURATION": ["ANTHROPIC_API_KEY", "CLAUDE_MODEL"],
                    "CHATGPT (OPENAI) CONFIGURATION": ["OPENAI_API_KEY"],
                    "EXECUTION MODE": ["EXECUTION_MODE"],
                    "WSL CONFIGURATION": ["WSL_DISTRIBUTION"],
                    "SSH CONFIGURATION": ["SSH_HOST", "SSH_USER", "SSH_PORT", "SSH_KEY_PATH", "SSH_PASSWORD"]
                }

                written_keys = set()

                for section_name, section_keys in sections.items():
                    # Vérifier si la section a des valeurs
                    has_values = any(key in env_data for key in section_keys)

                    if has_values:
                        f.write(f"# {'=' * 76}\n")
                        f.write(f"# {section_name}\n")
                        f.write(f"# {'=' * 76}\n")

                        for key in section_keys:
                            if key in env_data:
                                value = env_data[key]
                                # Échapper les valeurs si nécessaire
                                if ' ' in value or '"' in value:
                                    value = f'"{value}"'
                                f.write(f"{key}={value}\n")
                                written_keys.add(key)

                        f.write("\n")

                # Écrire les clés restantes
                remaining_keys = set(env_data.keys()) - written_keys
                if remaining_keys:
                    f.write(f"# {'=' * 76}\n")
                    f.write(f"# AUTRES VARIABLES\n")
                    f.write(f"# {'=' * 76}\n")
                    for key in sorted(remaining_keys):
                        value = env_data[key]
                        if ' ' in value or '"' in value:
                            value = f'"{value}"'
                        f.write(f"{key}={value}\n")

            logger.info(f"Fichier {env_file} écrit avec succès")
            return True

        except Exception as e:
            logger.error(f"Erreur lors de l'écriture de {env_file}: {e}")
            return False


# Instance singleton globale
_env_manager = EnvironmentManager()


def get_environment_manager() -> EnvironmentManager:
    """Retourne l'instance globale du gestionnaire d'environnements."""
    return _env_manager
