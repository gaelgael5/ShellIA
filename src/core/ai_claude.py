# core/ai_claude.py

from .ai_interface import AIProvider
from typing import List, Dict
import json

# API Anthropic pour Claude
from anthropic import Anthropic

class ClaudeProvider(AIProvider):
    """
    Implémentation de l'interface AIProvider pour Claude (Anthropic).
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        """
        Initialise le client Claude.

        Args:
            api_key: Clé API Anthropic
            model: Modèle Claude à utiliser (par défaut: claude-sonnet-4-20250514)
                   Options: claude-opus-4-20250514, claude-sonnet-4-20250514, claude-haiku-4-20250514
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def ask(self, context: List[Dict], user_message: str) -> Dict:
        """
        Envoie une requête à Claude et retourne la réponse en Markdown.

        Args:
            context: Historique des commandes exécutées
            user_message: Question de l'utilisateur

        Returns:
            Dict avec clé "markdown" contenant la réponse formatée
        """

        # Construit le prompt système
        system_prompt = """Tu es un assistant expert en administration Linux et systèmes Unix.

**RÈGLES IMPORTANTES :**
1. Tu ne dois JAMAIS exécuter de commande toi-même
2. Tu réponds UNIQUEMENT en Markdown pour une mise en page professionnelle
3. Tu es précis, concis et pédagogique dans tes explications

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
- **"high"** : Suppressions, arrêts système, modifications critiques (rm -rf, reboot, dd, etc.)

**APPROCHE :**
1. Analyse toujours le contexte des commandes précédentes si disponible
2. Propose d'abord des commandes de diagnostic avant des actions destructives
3. Explique clairement ce que tu proposes et pourquoi
4. Avertis explicitement des risques pour les commandes medium/high"""

        # Construit l'historique de contexte
        context_text = ""
        if context:
            context_text = "**Contexte des commandes précédemment exécutées :**\n\n"
            for c in context:
                context_text += f"```bash\n$ {c['command']}\n```\n"
                if c['stdout']:
                    context_text += f"**stdout:**\n```\n{c['stdout']}\n```\n"
                if c['stderr']:
                    context_text += f"**stderr:**\n```\n{c['stderr']}\n```\n"
                context_text += "\n---\n\n"
        else:
            context_text = "(Aucune commande précédente)\n\n"

        # Construction du prompt utilisateur
        user_prompt = f"""{context_text}**Demande de l'utilisateur :**

{user_message}"""

        # Appel API Claude
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_prompt
                    }
                ]
            )

            # Extraction du contenu de la réponse
            content = response.content[0].text

            # Retourne le Markdown brut pour parsing côté client
            return {
                "markdown": content
            }

        except Exception as e:
            # En cas d'erreur, retourne un message formaté
            error_markdown = f"""## ❌ Erreur API Claude

Une erreur s'est produite lors de la communication avec l'API Claude :

```
{str(e)}
```

**Suggestions :**
- Vérifiez que votre clé API est valide
- Vérifiez votre connexion internet
- Consultez les logs pour plus de détails"""

            return {
                "markdown": error_markdown
            }
