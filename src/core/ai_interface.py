# core/ai_interface.py

from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class AIProvider(ABC):
    """Interface pour tout moteur IA."""

    @abstractmethod
    def ask(self, context: List[Dict], user_message: str,
            chat_history: List[Dict] = None,
            system_profile: Optional[str] = None) -> Dict:
        """
        context: liste d'éléments dict {"command": str, "stdout": str, "stderr": str}
        user_message: texte du problème
        chat_history: historique [{role: "user"|"assistant", content: str}]
        system_profile: prompt du profil actif (injecté dans le system prompt)
        """
        pass
