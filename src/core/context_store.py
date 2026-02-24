# core/context_store.py

from typing import List, Dict, Optional


class ContextStore:
    """
    Historise les commandes exécutées et leurs résultats,
    ainsi que l'historique des échanges avec l'IA.
    """

    def __init__(self):
        self.history: List[Dict] = []
        self.chat_history: List[Dict] = []
        self.active_profile: Optional[Dict] = None

    def add(self, command: str, stdout: str, stderr: str):
        self.history.append({
            "command": command,
            "stdout": stdout,
            "stderr": stderr
        })

    def add_chat(self, role: str, content: str):
        """Ajoute un message à l'historique de la conversation IA."""
        self.chat_history.append({"role": role, "content": content})

    def get(self) -> List[Dict]:
        return self.history

    def get_chat_history(self) -> List[Dict]:
        return self.chat_history

    def set_active_profile(self, profile: Optional[Dict]):
        self.active_profile = profile

    def get_active_profile(self) -> Optional[Dict]:
        return self.active_profile

    def clear_chat(self):
        """Réinitialise l'historique de conversation IA."""
        self.chat_history = []
