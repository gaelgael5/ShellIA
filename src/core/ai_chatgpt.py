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

        system_prompt = """You are a Linux system administration assistant.
You must NEVER execute commands yourself.
You respond in Markdown for consistent and professional formatting.

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

You can add Markdown text before and after the JSON block to explain your analysis.
Use headings (##), lists, inline code with `backticks`, and formatting for better readability.

IMPORTANT:
- Always assess risk level: "low" (read-only), "medium" (modifications), "high" (deletions, service stops)
- Be precise in your commands
- Clearly explain what you are proposing
- You are in a continuous conversation — take the context of previous exchanges into account"""

        if system_profile:
            system_prompt += f"\n\n**Active profile context:**\n{system_profile}"

        messages = [{"role": "system", "content": system_prompt}]

        # Ajouter l'historique de conversation
        if chat_history:
            for msg in chat_history:
                if msg.get("role") in ("user", "assistant") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})

        # Build user message with recent shell context
        context_text = ""
        recent_context = context[-5:] if len(context) > 5 else context  # last 5 commands
        for c in recent_context:
            context_text += f"$ {c['command']}\nstdout:\n{c['stdout']}\nstderr:\n{c['stderr']}\n\n"

        user_prompt = user_message
        if context_text:
            user_prompt = f"Recent terminal commands:\n{context_text}\n{user_message}"

        messages.append({"role": "user", "content": user_prompt})

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )

        content = response.choices[0].message.content
        return {"markdown": content}
