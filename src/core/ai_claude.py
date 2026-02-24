# core/ai_claude.py

from .ai_interface import AIProvider
from typing import List, Dict, Optional
from anthropic import Anthropic


class ClaudeProvider(AIProvider):
    """Implémentation de l'interface AIProvider pour Claude (Anthropic)."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def ask(self, context: List[Dict], user_message: str,
            chat_history: List[Dict] = None,
            system_profile: Optional[str] = None) -> Dict:

        system_prompt = """Tu es un assistant expert en administration Linux et systèmes Unix.

**RÈGLES IMPORTANTES :**
1. Tu ne dois JAMAIS exécuter de commande toi-même
2. Tu réponds UNIQUEMENT en Markdown pour une mise en page professionnelle
3. Tu es précis, concis et pédagogique dans tes explications
4. Tu es dans une conversation continue — prends en compte tout l'historique des échanges

**FORMAT DE RÉPONSE :**

Quand tu proposes des commandes à exécuter, tu DOIS les formater dans un bloc JSON comme ceci :

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

**UTILISATION DU MARKDOWN :**
- Utilise `##` pour les titres principaux, `###` pour les sous-sections
- Utilise des listes à puces (`-`) pour énumérer
- Utilise du code inline avec `backticks` pour les commandes, fichiers, variables
- Utilise **gras** pour mettre en évidence les points importants
- Utilise des emojis pertinents : 💡 (conseil), ⚠️ (attention), 🚨 (danger), ✅ (ok)

**ÉVALUATION DES RISQUES :**
- **"low"** : Commandes de lecture seule (ls, cat, df, ps, systemctl status, etc.)
- **"medium"** : Modifications réversibles (systemctl restart, chmod, édition de fichiers)
- **"high"** : Suppressions, arrêts système, modifications critiques (rm -rf, reboot, dd, etc.)"""

        if system_profile:
            system_prompt += f"\n\n**Contexte d'utilisation (profil actif) :**\n{system_profile}"

        # Construire les messages multi-tour
        messages = []

        # Ajouter l'historique de conversation
        if chat_history:
            for msg in chat_history:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        # Construire le message utilisateur final avec contexte shell récent
        context_text = ""
        recent_context = context[-5:] if len(context) > 5 else context
        if recent_context:
            context_text = "**Commandes récentes dans le terminal :**\n\n"
            for c in recent_context:
                context_text += f"```bash\n$ {c['command']}\n```\n"
                if c['stdout']:
                    context_text += f"```\n{c['stdout']}\n```\n"
                if c['stderr']:
                    context_text += f"**stderr:** `{c['stderr'].strip()}`\n"
                context_text += "\n"

        user_content = user_message
        if context_text:
            user_content = f"{context_text}\n**Demande :** {user_message}"

        messages.append({"role": "user", "content": user_content})

        # Vérifier qu'on n'a pas deux messages consécutifs du même rôle
        # (contrainte Anthropic : doit alterner user/assistant)
        cleaned = []
        for msg in messages:
            if cleaned and cleaned[-1]["role"] == msg["role"]:
                # Fusionner avec le message précédent
                cleaned[-1]["content"] += "\n\n" + msg["content"]
            else:
                cleaned.append(msg)

        # S'assurer que le premier message est "user"
        if cleaned and cleaned[0]["role"] == "assistant":
            cleaned = cleaned[1:]
        if not cleaned:
            cleaned = [{"role": "user", "content": user_content}]

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=cleaned
            )
            content = response.content[0].text
            return {"markdown": content}

        except Exception as e:
            error_markdown = f"""## ❌ Erreur API Claude

```
{str(e)}
```"""
            return {"markdown": error_markdown}
