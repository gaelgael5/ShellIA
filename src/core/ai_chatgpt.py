# core/ai_chatgpt.py

from .ai_interface import AIProvider
from typing import List, Dict, Optional
from openai import OpenAI


class ChatGPTProvider(AIProvider):
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    def ask(self, context: List[Dict], user_message: str,
            chat_history: List[Dict] = None,
            system_profile: Optional[str] = None) -> Dict:

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
- Explique clairement ce que tu proposes
- Tu es dans une conversation continue — prends en compte le contexte des échanges précédents"""

        if system_profile:
            system_prompt += f"\n\n**Contexte d'utilisation (profil actif) :**\n{system_profile}"

        messages = [{"role": "system", "content": system_prompt}]

        # Ajouter l'historique de conversation
        if chat_history:
            for msg in chat_history:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        # Construire le message utilisateur avec le contexte shell récent
        context_text = ""
        recent_context = context[-5:] if len(context) > 5 else context  # 5 dernières commandes
        for c in recent_context:
            context_text += f"$ {c['command']}\nstdout:\n{c['stdout']}\nstderr:\n{c['stderr']}\n\n"

        user_prompt = user_message
        if context_text:
            user_prompt = f"Commandes récentes dans le terminal :\n{context_text}\n{user_message}"

        messages.append({"role": "user", "content": user_prompt})

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        content = response.choices[0].message.content
        return {"markdown": content}
