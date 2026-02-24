# core/ssh_executor.py

import paramiko
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SSHExecutor:
    """
    Exécute des commandes sur une machine distante via SSH.
    """

    def __init__(
        self,
        host: str,
        username: str,
        port: int = 22,
        key_path: Optional[str] = None,
        password: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialise la connexion SSH.

        Args:
            host: Adresse IP ou hostname de la machine distante
            username: Nom d'utilisateur SSH
            port: Port SSH (par défaut 22)
            key_path: Chemin vers la clé privée SSH (optionnel)
            password: Mot de passe SSH (optionnel, ignoré si key_path est fourni)
            timeout: Timeout de connexion en secondes
        """
        self.host = host
        self.username = username
        self.port = port
        self.key_path = key_path
        self.password = password
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None

    def connect(self) -> bool:
        """
        Établit la connexion SSH.

        Returns:
            True si la connexion réussit, False sinon
        """
        try:
            self.client = paramiko.SSHClient()

            # Accepte automatiquement les clés d'hôte inconnues
            # ⚠️ En production, utilisez plutôt load_system_host_keys() et set_missing_host_key_policy(RejectPolicy)
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            # Connexion avec clé privée ou mot de passe
            if self.key_path:
                logger.info(f"Connexion SSH à {self.username}@{self.host}:{self.port} avec clé privée")
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=self.timeout,
                    look_for_keys=False,
                    allow_agent=False
                )
            elif self.password:
                logger.info(f"Connexion SSH à {self.username}@{self.host}:{self.port} avec mot de passe")
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=self.timeout,
                    look_for_keys=False,  # Ne pas chercher de clés si on utilise un mot de passe
                    allow_agent=False     # Ne pas utiliser l'agent SSH
                )
            else:
                # Essaie avec l'agent SSH ou les clés par défaut
                logger.info(f"Connexion SSH à {self.username}@{self.host}:{self.port} avec agent SSH")
                self.client.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    timeout=self.timeout
                )

            logger.info(f"✅ Connecté à {self.host}")
            return True

        except paramiko.AuthenticationException:
            logger.error(f"❌ Authentification SSH échouée pour {self.username}@{self.host}")
            return False
        except paramiko.SSHException as e:
            logger.error(f"❌ Erreur SSH: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur de connexion: {e}")
            return False

    def execute(self, command: str, timeout: int = 30) -> Dict:
        """
        Exécute une commande sur la machine distante.

        Args:
            command: Commande shell à exécuter
            timeout: Timeout d'exécution en secondes

        Returns:
            Dictionnaire avec stdout, stderr, return_code, success
        """
        # Connexion si pas déjà connecté
        if not self.client or not self.client.get_transport() or not self.client.get_transport().is_active():
            if not self.connect():
                return {
                    "stdout": "",
                    "stderr": "Impossible de se connecter au serveur SSH",
                    "return_code": -1,
                    "success": False
                }

        try:
            logger.info(f"Exécution SSH: {command}")

            # Exécute la commande
            stdin, stdout, stderr = self.client.exec_command(command, timeout=timeout)

            # Récupère les résultats
            exit_code = stdout.channel.recv_exit_status()
            stdout_text = stdout.read().decode('utf-8', errors='replace')
            stderr_text = stderr.read().decode('utf-8', errors='replace')

            return {
                "stdout": stdout_text,
                "stderr": stderr_text,
                "return_code": exit_code,
                "success": exit_code == 0
            }

        except paramiko.SSHException as e:
            logger.error(f"❌ Erreur SSH lors de l'exécution: {e}")
            return {
                "stdout": "",
                "stderr": f"Erreur SSH: {str(e)}",
                "return_code": -1,
                "success": False
            }
        except Exception as e:
            logger.error(f"❌ Erreur d'exécution: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "success": False
            }

    def disconnect(self):
        """
        Ferme la connexion SSH.
        """
        if self.client:
            self.client.close()
            logger.info(f"Déconnecté de {self.host}")

    def __del__(self):
        """
        Destructeur : ferme la connexion si elle est encore ouverte.
        """
        self.disconnect()
