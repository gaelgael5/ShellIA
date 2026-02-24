# core/ssh_executor.py

import paramiko
import time
import uuid
import select
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class SSHExecutor:
    """
    Exécute des commandes sur une machine distante via SSH.
    Utilise invoke_shell() pour une session persistante avec PTY,
    ce qui maintient le répertoire courant et les variables d'environnement.
    """

    def __init__(self, host: str, username: str, port: int = 22,
                 key_path: Optional[str] = None, password: Optional[str] = None,
                 timeout: int = 30):
        self.host = host
        self.username = username
        self.port = port
        self.key_path = key_path
        self.password = password
        self.timeout = timeout
        self.client: Optional[paramiko.SSHClient] = None
        self.channel: Optional[paramiko.Channel] = None

    def connect(self) -> bool:
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            if self.key_path:
                logger.info(f"Connexion SSH à {self.username}@{self.host}:{self.port} avec clé privée")
                self.client.connect(
                    hostname=self.host, port=self.port, username=self.username,
                    key_filename=self.key_path, timeout=self.timeout,
                    look_for_keys=False, allow_agent=False
                )
            elif self.password:
                logger.info(f"Connexion SSH à {self.username}@{self.host}:{self.port} avec mot de passe")
                self.client.connect(
                    hostname=self.host, port=self.port, username=self.username,
                    password=self.password, timeout=self.timeout,
                    look_for_keys=False, allow_agent=False
                )
            else:
                self.client.connect(
                    hostname=self.host, port=self.port, username=self.username,
                    timeout=self.timeout
                )

            # Créer un shell interactif persistant avec PTY (xterm-256color)
            self.channel = self.client.invoke_shell(
                term='xterm-256color', width=220, height=50
            )
            self.channel.setblocking(False)

            # Attendre et vider le banner de connexion
            time.sleep(0.5)
            self._flush()

            # Configurer le shell : désactiver le prompt et les couleurs interférentes
            self._send_raw("unset PROMPT_COMMAND; export PS1=''; export PS2=''; export TERM=xterm-256color\n")
            time.sleep(0.3)
            self._flush()

            logger.info(f"✅ Connecté à {self.host} (shell persistant PTY)")
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

    def _flush(self):
        """Vide le buffer de réception sans bloquer."""
        while True:
            try:
                r, _, _ = select.select([self.channel], [], [], 0.05)
                if not r:
                    break
                data = self.channel.recv(4096)
                if not data:
                    break
            except Exception:
                break

    def _send_raw(self, data: str):
        """Envoie des données brutes au channel SSH."""
        self.channel.sendall(data.encode('utf-8'))

    def _is_connected(self) -> bool:
        return (
            self.client is not None and
            self.client.get_transport() is not None and
            self.client.get_transport().is_active() and
            self.channel is not None and
            not self.channel.closed
        )

    def execute(self, command: str, timeout: int = 30) -> Dict:
        """Exécute une commande dans le shell persistant."""
        if not self._is_connected():
            logger.info("Session SSH perdue, reconnexion...")
            if not self.connect():
                return {
                    "stdout": "",
                    "stderr": "Impossible de se connecter au serveur SSH",
                    "return_code": -1,
                    "success": False
                }

        try:
            marker = f"___SHELLIA_END_{uuid.uuid4().hex}___"

            # Envoyer la commande puis le marker
            self._send_raw(f"{command}\necho {marker}\n")

            # Lire jusqu'au marker
            output = ""
            start = time.time()

            while True:
                if time.time() - start > timeout:
                    return {
                        "stdout": self._clean_ansi(output),
                        "stderr": f"Timeout après {timeout}s",
                        "return_code": -1,
                        "success": False
                    }

                try:
                    r, _, _ = select.select([self.channel], [], [], 0.1)
                    if r:
                        chunk = self.channel.recv(8192)
                        if chunk:
                            output += chunk.decode('utf-8', errors='replace')
                            if marker in output:
                                break
                    elif self.channel.closed:
                        break
                except Exception as e:
                    logger.error(f"Erreur lecture SSH: {e}")
                    break

            if marker in output:
                idx = output.find(marker)
                raw_stdout = output[:idx]

                # Nettoyer les séquences ANSI, normaliser les retours chariot
                stdout = self._clean_ansi(raw_stdout)
                stdout = stdout.replace('\r\n', '\n').replace('\r', '\n')

                # Supprimer l'écho de la commande (première ligne si identique)
                lines = stdout.split('\n')
                cleaned_lines = []
                skip_next = True
                for line in lines:
                    # Ignorer l'écho de la commande et du echo marker
                    if skip_next and (command.strip() in line or line.strip() == command.strip()):
                        skip_next = False
                        continue
                    if f"echo {marker}" in line:
                        continue
                    cleaned_lines.append(line)

                stdout_clean = '\n'.join(cleaned_lines).strip()

                return {
                    "stdout": stdout_clean + '\n' if stdout_clean else '',
                    "stderr": "",
                    "return_code": 0,
                    "success": True
                }
            else:
                return {
                    "stdout": self._clean_ansi(output),
                    "stderr": "Connexion perdue ou erreur inattendue",
                    "return_code": -1,
                    "success": False
                }

        except Exception as e:
            logger.error(f"❌ Erreur d'exécution SSH: {e}")
            return {
                "stdout": "",
                "stderr": str(e),
                "return_code": -1,
                "success": False
            }

    @staticmethod
    def _clean_ansi(text: str) -> str:
        """Supprime les séquences d'échappement ANSI/VT100."""
        import re
        ansi_escape = re.compile(
            r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])'
        )
        return ansi_escape.sub('', text)

    def disconnect(self):
        if self.channel:
            try:
                self.channel.close()
            except Exception:
                pass
            self.channel = None
        if self.client:
            try:
                self.client.close()
            except Exception:
                pass
            self.client = None
        logger.info(f"Déconnecté de {self.host}")

    def __del__(self):
        self.disconnect()
