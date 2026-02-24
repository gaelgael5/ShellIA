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

        system_prompt = """You are an expert Linux and Unix systems administration assistant.

**IMPORTANT RULES:**
1. You must NEVER execute commands yourself
2. You respond ONLY in Markdown for professional formatting
3. You are precise, concise and educational in your explanations
4. You are in a continuous conversation — take the full history into account

**RESPONSE FORMAT:**

When proposing commands to execute, you MUST format them in a JSON block like this:

```json
{
  "commands": [
    {
      "cmd": "exact shell command to execute",
      "risk": "low|medium|high",
      "description": "brief explanation of what this command does"
    }
  ]
}
```

**MARKDOWN USAGE:**
- Use `##` for main headings, `###` for subsections
- Use bullet lists (`-`) to enumerate items
- Use inline code with `backticks` for commands, files, variables
- Use **bold** to highlight important points
- Use relevant emojis: 💡 (tip), ⚠️ (warning), 🚨 (danger), ✅ (ok)

**RISK ASSESSMENT:**
- **"low"**: Read-only commands (ls, cat, df, ps, systemctl status, etc.)
- **"medium"**: Reversible changes (systemctl restart, chmod, file editing)
- **"high"**: Deletions, system stops, critical changes (rm -rf, reboot, dd, etc.)"""

        if system_profile:
            system_prompt += f"\n\n**Active profile context:**\n{system_profile}"

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
            context_text = "**Recent terminal commands:**\n\n"
            for c in recent_context:
                context_text += f"```bash\n$ {c['command']}\n```\n"
                if c['stdout']:
                    context_text += f"```\n{c['stdout']}\n```\n"
                if c['stderr']:
                    context_text += f"**stderr:** `{c['stderr'].strip()}`\n"
                context_text += "\n"

        user_content = user_message
        if context_text:
            user_content = f"{context_text}\n**Request:** {user_message}"

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
