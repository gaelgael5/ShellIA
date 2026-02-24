# Configuration et utilisation de Claude

Ce guide explique comment utiliser Claude (Anthropic) au lieu de ChatGPT dans ShellIA.

## 📋 Table des matières

1. [Installation des dépendances](#installation-des-dépendances)
2. [Configuration de la clé API](#configuration-de-la-clé-api)
3. [Choix du provider](#choix-du-provider)
4. [Modèles disponibles](#modèles-disponibles)
5. [Comparaison ChatGPT vs Claude](#comparaison-chatgpt-vs-claude)

---

## 🔧 Installation des dépendances

Pour utiliser Claude, vous devez installer la bibliothèque `anthropic` :

```bash
pip install anthropic
```

Ou ajoutez-la à votre `requirements.txt` :

```txt
anthropic>=0.39.0
```

---

## 🔑 Configuration de la clé API

### 1. Obtenir une clé API Anthropic

1. Créez un compte sur [console.anthropic.com](https://console.anthropic.com)
2. Allez dans **Settings** > **API Keys**
3. Créez une nouvelle clé API
4. Copiez la clé (elle commence par `sk-ant-...`)

### 2. Configurer la clé API

**Linux / Mac :**

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-votre-clé-ici"
export AI_PROVIDER="claude"
```

**Windows (CMD) :**

```cmd
set ANTHROPIC_API_KEY=sk-ant-api03-votre-clé-ici
set AI_PROVIDER=claude
```

**Windows (PowerShell) :**

```powershell
$env:ANTHROPIC_API_KEY="sk-ant-api03-votre-clé-ici"
$env:AI_PROVIDER="claude"
```

**Fichier `.env` (recommandé) :**

Créez un fichier `.env` à la racine du projet :

```env
# Choisir le provider : chatgpt ou claude
AI_PROVIDER=claude

# Pour Claude
ANTHROPIC_API_KEY=sk-ant-api03-votre-clé-ici
CLAUDE_MODEL=claude-sonnet-4-20250514

# Pour ChatGPT (si vous voulez basculer)
OPENAI_API_KEY=sk-votre-clé-openai
```

Puis installez `python-dotenv` :

```bash
pip install python-dotenv
```

Et ajoutez au début de [main.py](main.py) :

```python
from dotenv import load_dotenv
load_dotenv()  # Charge le fichier .env
```

---

## 🔄 Choix du provider

Le choix du provider se fait via la variable d'environnement `AI_PROVIDER` :

| Valeur | Provider | Clé API requise |
|--------|----------|----------------|
| `chatgpt` | OpenAI ChatGPT | `OPENAI_API_KEY` |
| `claude` | Anthropic Claude | `ANTHROPIC_API_KEY` |

### Exemple : Basculer entre providers

```bash
# Utiliser Claude
export AI_PROVIDER=claude
export ANTHROPIC_API_KEY=sk-ant-...
uvicorn main:app --reload

# Utiliser ChatGPT
export AI_PROVIDER=chatgpt
export OPENAI_API_KEY=sk-...
uvicorn main:app --reload
```

---

## 🤖 Modèles disponibles

### Modèles Claude (Anthropic)

Vous pouvez choisir le modèle Claude via la variable `CLAUDE_MODEL` :

| Modèle | ID | Performance | Coût | Cas d'usage |
|--------|-----|-------------|------|-------------|
| **Claude Opus 4** | `claude-opus-4-20250514` | ⭐⭐⭐⭐⭐ | 💰💰💰 | Tâches complexes, analyse approfondie |
| **Claude Sonnet 4** | `claude-sonnet-4-20250514` | ⭐⭐⭐⭐ | 💰💰 | **Recommandé** - Équilibre perf/coût |
| **Claude Haiku 4** | `claude-haiku-4-20250514` | ⭐⭐⭐ | 💰 | Rapide, tâches simples |

**Défaut :** `claude-sonnet-4-20250514` (meilleur équilibre)

### Modèles ChatGPT (OpenAI)

Le code utilise `gpt-4o-mini` par défaut. Pour changer, modifiez [core/ai_chatgpt.py:55](core/ai_chatgpt.py#L55).

---

## ⚖️ Comparaison ChatGPT vs Claude

| Critère | ChatGPT (gpt-4o-mini) | Claude (Sonnet 4) |
|---------|----------------------|-------------------|
| **Précision commandes Linux** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Contexte long** | 128k tokens | 200k tokens |
| **Formatage Markdown** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Sécurité** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Coût** | 💰 | 💰💰 |
| **Rapidité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Recommandation :**
- **Claude Sonnet 4** : Meilleure qualité de réponse pour administration Linux
- **ChatGPT gpt-4o-mini** : Plus rapide et moins cher

---

## 🚀 Lancement avec Claude

### Méthode 1 : Variables d'environnement

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
export AI_PROVIDER="claude"
export CLAUDE_MODEL="claude-sonnet-4-20250514"

cd d:\srcs\ShellIA\src
uvicorn main:app --reload
```

### Méthode 2 : Fichier .env

Créez `.env` :

```env
AI_PROVIDER=claude
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-20250514
```

Puis lancez :

```bash
cd d:\srcs\ShellIA\src
uvicorn main:app --reload
```

Vous devriez voir :

```
✅ Utilisation de Claude (claude-sonnet-4-20250514)
INFO:     Started server process [12345]
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 🧪 Tester Claude

1. Ouvrez http://localhost:8000
2. Tapez une question : "Vérifie l'espace disque disponible"
3. Claude devrait répondre en Markdown formaté avec des commandes

**Exemple de réponse attendue :**

```markdown
## Vérification de l'espace disque

Pour vérifier l'espace disque, je vous recommande cette commande :

```json
{
  "commands": [
    {
      "cmd": "df -h",
      "risk": "low",
      "description": "Affiche l'utilisation de l'espace disque"
    }
  ]
}
```

Cette commande est sans risque et donne un aperçu complet.
```

---

## 🔧 Dépannage

### Erreur : "ANTHROPIC_API_KEY doit être défini"

```
ValueError: ANTHROPIC_API_KEY doit être défini pour utiliser Claude
```

**Solution :** Définissez la variable d'environnement :

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-..."
```

### Erreur : "No module named 'anthropic'"

```
ModuleNotFoundError: No module named 'anthropic'
```

**Solution :** Installez la bibliothèque :

```bash
pip install anthropic
```

### Claude ne répond pas / timeout

**Solutions possibles :**
1. Vérifiez votre connexion internet
2. Vérifiez que votre clé API est valide
3. Vérifiez les limites de votre compte Anthropic
4. Essayez un modèle plus rapide (`claude-haiku-4-20250514`)

---

## 📊 Tarification

**Prix indicatifs (susceptibles de changer) :**

| Modèle | Input (par million tokens) | Output (par million tokens) |
|--------|---------------------------|----------------------------|
| Claude Opus 4 | ~$15 | ~$75 |
| Claude Sonnet 4 | ~$3 | ~$15 |
| Claude Haiku 4 | ~$0.25 | ~$1.25 |
| GPT-4o-mini | ~$0.15 | ~$0.60 |

💡 **Astuce :** Pour un usage personnel/test, Claude Sonnet 4 offre le meilleur rapport qualité/prix.

---

## 🔐 Sécurité

**Ne commitez JAMAIS vos clés API dans Git !**

Ajoutez à `.gitignore` :

```gitignore
.env
*.env
.env.local
```

**Bonnes pratiques :**
- Stockez les clés dans des variables d'environnement
- Utilisez un fichier `.env` pour le développement
- Utilisez des secrets managers en production
- Révoquez immédiatement les clés compromises

---

## 📚 Ressources

- [Documentation API Claude](https://docs.anthropic.com/claude/reference)
- [Console Anthropic](https://console.anthropic.com)
- [Pricing Claude](https://www.anthropic.com/pricing)
- [Bibliothèque Python Anthropic](https://github.com/anthropics/anthropic-sdk-python)

---

**Besoin d'aide ?** Consultez les logs d'erreur ou vérifiez la [documentation Anthropic](https://docs.anthropic.com).
