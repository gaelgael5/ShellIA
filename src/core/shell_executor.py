# core/shell_executor.py

import subprocess
from typing import Dict, Optional
import logging
import sys
import uuid
import pexpect
from pexpect.popen_spawn import PopenSpawn

from . import secret_manager
from .ssh_executor import SSHExecutor

logger = logging.getLogger(__name__)


class ShellExecutor:
    """
    Exécute des commandes shell localement ou à distance via SSH.
    Maintient une session persistante pour local et WSL avec pexpect.
    """

    def __init__(
        self,
        mode: str = "local",
        ssh_host: Optional[str] = None,
        ssh_user: Optional[str] = None,
        ssh_port: int = 22,
        ssh_key_path: Optional[str] = None,
        ssh_password: Optional[str] = None,
        wsl_distribution: Optional[str] = None
    ):
        """
        Initialise l'executor.

        Args:
            mode: "local" pour exécution locale, "remote" pour SSH, "wsl" pour WSL
            ssh_host: Adresse de la machine distante (requis si mode=remote)
            ssh_user: Nom d'utilisateur SSH (requis si mode=remote)
            ssh_port: Port SSH (par défaut 22)
            ssh_key_path: Chemin vers la clé privée SSH
            ssh_password: Mot de passe SSH
            wsl_distribution: Distribution WSL à utiliser (optionnel, par défaut la distribution par défaut)
        """
        self.mode = mode.lower()
        self.ssh_executor: Optional[SSHExecutor] = None
        self.wsl_distribution = wsl_distribution

        # Session persistante pour local et WSL (utilise pexpect)
        self.persistent_session: Optional[PopenSpawn] = None

        if self.mode == "remote":
            if not ssh_host or not ssh_user:
                raise ValueError("ssh_host et ssh_user sont requis en mode remote")

            logger.info(f"🌐 Mode distant activé: {ssh_user}@{ssh_host}:{ssh_port}")
            self.ssh_executor = SSHExecutor(
                host=ssh_host,
                username=ssh_user,
                port=ssh_port,
                key_path=ssh_key_path,
                password=ssh_password
            )
            # Connexion immédiate
            if not self.ssh_executor.connect():
                raise ConnectionError(f"Impossible de se connecter à {ssh_host}")
        elif self.mode == "wsl":
            if wsl_distribution:
                logger.info(f"🐧 Mode WSL activé: {wsl_distribution}")
            else:
                logger.info("🐧 Mode WSL activé (distribution par défaut)")
            self._start_persistent_wsl_session()
        else:
            logger.info("💻 Mode local activé")
            self._start_persistent_local_session()

    def _start_persistent_wsl_session(self):
        """Démarre une session bash persistante dans WSL avec pexpect."""
        try:
            # Commande WSL
            if self.wsl_distribution:
                wsl_cmd = f'wsl.exe -d {self.wsl_distribution} -- bash --norc --noprofile'
            else:
                wsl_cmd = 'wsl.exe -- bash --norc --noprofile'

            # Créer la session avec pexpect PopenSpawn (compatible Windows)
            # IMPORTANT : linesep='\n' pour envoyer des fins de ligne Unix au bash de WSL
            # cwd='C:\\' évite l'erreur "Failed to translate" au démarrage
            self.persistent_session = PopenSpawn(
                wsl_cmd,
                timeout=30,
                encoding='utf-8',
                codec_errors='replace',
                cwd='C:\\'
            )
            # Forcer les fins de ligne Unix
            self.persistent_session.linesep = '\n'

            # Désactiver les prompts pour éviter les interférences
            self.persistent_session.sendline("PS1=''")
            self.persistent_session.sendline("PS2=''")

            # Aller dans le home directory
            self.persistent_session.sendline("cd ~")

            # Attendre un peu que bash soit prêt
            import time
            time.sleep(0.2)

            logger.info("✅ Session WSL persistante démarrée avec pexpect")
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage de la session WSL: {e}")
            raise

    def _start_persistent_local_session(self):
        """Démarre une session shell persistante locale avec pexpect."""
        try:
            # Détecter le shell selon le système
            if sys.platform == 'win32':
                shell_cmd = 'cmd.exe'
            else:
                shell_cmd = 'bash --norc --noprofile'

            # Créer la session avec pexpect PopenSpawn
            encoding = 'cp850' if sys.platform == 'win32' else 'utf-8'
            self.persistent_session = PopenSpawn(
                shell_cmd,
                timeout=30,
                encoding=encoding,
                codec_errors='replace'
            )

            # Forcer les fins de ligne appropriées
            if sys.platform != 'win32':
                # Unix : utiliser \n
                self.persistent_session.linesep = '\n'
            # Windows cmd.exe utilise \r\n par défaut

            # Configuration initiale
            if sys.platform != 'win32':
                # Pour bash : désactiver les prompts
                self.persistent_session.sendline("PS1=''")
                self.persistent_session.sendline("PS2=''")
            else:
                # Pour cmd.exe : désactiver le prompt
                self.persistent_session.sendline("prompt $S")

            # Attendre un peu que le shell soit prêt
            import time
            time.sleep(0.2)

            logger.info(f"✅ Session locale persistante démarrée avec pexpect ({shell_cmd})")
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage de la session locale: {e}")
            raise

    def execute(self, command: str, timeout: int = 30) -> Dict:
        """
        Exécute une commande (localement, à distance ou dans WSL).

        Args:
            command: Commande shell à exécuter
            timeout: Timeout en secondes

        Returns:
            Dictionnaire avec stdout, stderr, return_code, success
        """
        # Remplace les secrets avant exécution
        safe_command = secret_manager.replace_in_command(command)

        if self.mode == "remote":
            return self._execute_remote(safe_command, timeout)
        elif self.mode in ["wsl", "local"]:
            return self._execute_persistent(safe_command, timeout)
        else:
            return self._execute_persistent(safe_command, timeout)

    def _execute_persistent(self, command: str, timeout: int = 30) -> Dict:
        """Exécute une commande dans la session persistante (WSL ou local)."""
        if not self.persistent_session or self.persistent_session.proc.poll() is not None:
            return {
                "stdout": "",
                "stderr": "Session non initialisée ou terminée",
                "return_code": -1,
                "success": False
            }

        try:
            # Générer un marker unique
            marker = f"___SHELLIA_END_{uuid.uuid4().hex}___"

            # Envoyer la commande suivie du marker
            self.persistent_session.sendline(command)
            self.persistent_session.sendline(f"echo {marker}")

            # Attendre le marker avec pexpect
            try:
                index = self.persistent_session.expect([marker, pexpect.EOF, pexpect.TIMEOUT], timeout=timeout)

                if index == 0:
                    # Marker trouvé - succès
                    # Récupérer la sortie avant le marker
                    output = self.persistent_session.before

                    # Nettoyer la sortie : retirer la commande echo et les newlines superflus
                    lines = output.split('\n')
                    # Retirer la première ligne (la commande elle-même) et les lignes vides au début/fin
                    if lines and lines[0].strip() == command.strip():
                        lines = lines[1:]

                    stdout = '\n'.join(lines).strip()

                    return {
                        "stdout": stdout + '\n' if stdout else '',
                        "stderr": "",
                        "return_code": 0,
                        "success": True
                    }
                elif index == 1:
                    # EOF - session terminée
                    return {
                        "stdout": "",
                        "stderr": "Session terminée inopinément",
                        "return_code": -1,
                        "success": False
                    }
                else:
                    # Timeout
                    return {
                        "stdout": self.persistent_session.before,
                        "stderr": f"Timeout après {timeout}s",
                        "return_code": -1,
                        "success": False
                    }

            except Exception as e:
                logger.error(f"Erreur lors de l'attente du marqueur: {e}")
                return {
                    "stdout": "",
                    "stderr": str(e),
                    "return_code": -1,
                    "success": False
                }

        except Exception as e:
            logger.error(f"Erreur lors de l'exécution: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "success": False
            }

    def _execute_remote(self, command: str, timeout: int = 30) -> Dict:
        """Exécute une commande à distance via SSH."""
        if not self.ssh_executor:
            return {
                "stdout": "",
                "stderr": "SSH executor non initialisé",
                "return_code": -1,
                "success": False
            }

        return self.ssh_executor.execute(command, timeout)

    def disconnect(self):
        """Ferme la connexion SSH ou la session persistante si elle est active."""
        if self.ssh_executor:
            self.ssh_executor.disconnect()

        # Fermer la session persistante
        if self.persistent_session and self.persistent_session.proc.poll() is None:
            try:
                self.persistent_session.sendline("exit")
                self.persistent_session.close()
                logger.info("Session persistante fermée")
            except Exception as e:
                logger.error(f"Erreur lors de la fermeture de la session: {e}")
                try:
                    self.persistent_session.terminate(force=True)
                except:
                    pass

            self.persistent_session = None

    def __del__(self):
        """Destructeur : ferme les sessions si elles sont encore ouvertes."""
        self.disconnect()
