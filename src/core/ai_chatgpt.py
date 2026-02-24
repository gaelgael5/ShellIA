# core/ai_chatgpt.py

from .ai_interface import AIProvider
from typing import List, Dict
import json

# Nouvelle API OpenAI (>= 1.0.0)
from openai import OpenAI

class ChatGPTProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def ask(self, context: List[Dict], user_message: str) -> Dict:
        # Construit le prompt système
        system_prompt = """Tu es un assistant d'administration Linux.
Tu ne dois JAMAIS exécuter de commande.
Tu réponds en Markdown pour une mise en page cohérente et professionnelle.

Quand tu proposes des commandes à exécuter, tu DOIS les formater dans un bloc JSON ainsi :

```json
{
  "commands": [
    {
      "cmd": "commande shell exacte à exécuter",
      "risk": "low|medium|high",
      "description": "explication courte de ce que fait cette commande"
    }
  ]
}
```

Tu peux ajouter du texte Markdown avant et après le bloc JSON pour expliquer ton analyse.
Utilise des titres (##), des listes, du code inline avec `backticks`, et du formatage pour une meilleure lisibilité.

IMPORTANT :
- Évalue toujours le niveau de risque : "low" (lecture seule), "medium" (modifications), "high" (suppressions, arrêts de service)
- Sois précis dans tes commandes
- Explique clairement ce que tu proposes"""

        # Construit l'historique de contexte
        context_text = ""
        for c in context:
            context_text += f"$ {c['command']}\nstdout:\n{c['stdout']}\nstderr:\n{c['stderr']}\n\n"

        user_prompt = f"""Contexte des commandes précédentes :
{context_text if context_text else "(aucune commande précédente)"}

Demande de l'utilisateur :
{user_message}"""

        # Appel API OpenAI moderne
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )

        content = response.choices[0].message.content

        # Retourne le Markdown brut pour parsing côté client
        return {
            "markdown": content
        }
