# core/context_store.py

from typing import List, Dict

class ContextStore:
    """
    Historise les commandes exécutées et leurs résultats.
    """
    def __init__(self):
        self.history: List[Dict] = []

    def add(self, command: str, stdout: str, stderr: str):
        self.history.append({
            "command": command,
            "stdout": stdout,
            "stderr": stderr
        })

    def get(self) -> List[Dict]:
        return self.history
