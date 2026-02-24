# core/ai_interface.py

from abc import ABC, abstractmethod
from typing import List, Dict

class AIProvider(ABC):
    """
    Interface pour tout moteur IA.
    """

    @abstractmethod
    def ask(self, context: List[Dict], user_message: str) -> Dict:
        """
        context: liste d'éléments dict {"command": str, "stdout": str, "stderr": str}
        user_message: texte du problème
        Retourne un dict avec la structure :
        {
          "explanation": str,
          "commands": [
            {"cmd": str, "risk": "low|medium|high", "description": str}
          ],
          "notes": str
        }
        """
        pass
