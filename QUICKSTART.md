# 🚀 Guide de démarrage rapide - ShellIA

Guide pour lancer ShellIA avec ChatGPT ou Claude en quelques minutes.

## ⚡ Installation rapide

### 1. Installation des dépendances

```bash
cd d:\srcs\ShellIA
py -m pip install -r requirements.txt
```

Ou
```bash
cd d:\srcs\ShellIA
python -m pip install -r requirements.txt
```

Cela installera :
- FastAPI et Uvicorn (serveur web)
- OpenAI (pour ChatGPT)
- Anthropic (pour Claude)
- python-dotenv (gestion configuration)

---

## 🔑 Configuration (choisissez une option)

### Option A : Utiliser Claude (recommandé)

```bash
# Windows CMD
# Utilsez le site pour récupérer l'apiKey : https://console.anthropic.com
set ANTHROPIC_API_KEY=sk-ant-api03-votre-clé-ici
set AI_PROVIDER=claude

# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-api03-votre-clé-ici"
$env:AI_PROVIDER="claude"

# Linux / Mac
export ANTHROPIC_API_KEY="sk-ant-api03-votre-clé-ici"
export AI_PROVIDER="claude"
```

### Option B : Utiliser ChatGPT

```bash
# Windows CMD
set OPENAI_API_KEY=sk-votre-clé-openai
set AI_PROVIDER=chatgpt

# Windows PowerShell
$env:OPENAI_API_KEY="sk-votre-clé-openai"
$env:AI_PROVIDER="chatgpt"

# Linux / Mac
export OPENAI_API_KEY="sk-votre-clé-openai"
export AI_PROVIDER="chatgpt"
```

### Option C : Fichier .env (recommandé pour développement)

Créez un fichier `.env` à la racine du projet :

```env
# Choisir le provider
AI_PROVIDER=claude

# Claude
ANTHROPIC_API_KEY=sk-ant-api03-votre-clé-ici
CLAUDE_MODEL=claude-sonnet-4-20250514

# OU ChatGPT
# OPENAI_API_KEY=sk-votre-clé-openai
```

Puis modifiez le début de `src/main.py` :

```python
from dotenv import load_dotenv
load_dotenv()  # Ajouter cette ligne

# ... reste du code
```

---

## ▶️ Lancement du serveur

```bash
cd src
py -m uvicorn main:app --reload
```

Vous devriez voir :

```
✅ Utilisation de Claude (claude-sonnet-4-20250514)
INFO:     Uvicorn running on http://127.0.0.1:8000
```

ou

```
✅ Utilisation de ChatGPT (gpt-4o-mini)
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 🌐 Utilisation

1. Ouvrez votre navigateur : **http://localhost:8000**

2. Interface divisée en deux :
   - **Gauche** : Chat avec l'IA
   - **Droite** : Terminal

3. **Tapez une question** dans le panneau gauche :
   ```
   Vérifie l'espace disque disponible
   ```

4. **L'IA répond** en Markdown formaté avec des boutons de commandes

5. **Cliquez sur un bouton** → la commande est **copiée** dans le terminal

6. **Appuyez sur Entrée** pour **exécuter** la commande

7. **Le résultat** s'affiche dans le terminal et est renvoyé à l'IA pour contexte

---

## 📋 Exemples de questions

### Diagnostic système

```
Vérifie l'utilisation CPU et mémoire
Montre-moi les processus qui consomment le plus de ressources
Vérifie l'espace disque sur toutes les partitions
```

### Gestion de services

```
Le service nginx ne répond plus, aide-moi
Vérifie si Docker est en cours d'exécution
Redémarre le service Apache
```

### Réseau

```
Vérifie ma connexion réseau
Affiche mes interfaces réseau
Teste la connectivité vers google.com
```

### Fichiers et logs

```
Trouve les fichiers modifiés aujourd'hui dans /var/log
Montre-moi les 50 dernières lignes du syslog
Cherche les erreurs dans les logs nginx
```

---

## 🎨 Fonctionnalités

### ✅ Markdown riche
- Titres, listes, code formaté
- Explications pédagogiques
- Emojis pour la lisibilité

### 🎯 Niveaux de risque
- 🟢 **LOW** (vert) : Lecture seule
- 🟡 **MEDIUM** (jaune) : Modifications
- 🔴 **HIGH** (rouge clignotant) : Danger

### 🔐 Sécurité
- Cliquer = copie (pas d'exécution)
- Validation explicite avec Entrée
- Avertissements pour commandes à risque

### 📊 Contexte
- L'IA voit l'historique des commandes
- Suggestions adaptées au contexte
- Diagnostic itératif

---

## 🛑 Arrêt du serveur

Appuyez sur `Ctrl+C` dans le terminal où uvicorn tourne.

---

## 🔧 Dépannage

### "ANTHROPIC_API_KEY doit être défini"

➡️ Définissez la variable d'environnement ou créez un fichier `.env`

### "No module named 'anthropic'"

➡️ Installez les dépendances :
```bash
pip install -r requirements.txt
```

### L'IA ne répond pas

➡️ Vérifiez :
1. Votre clé API est valide
2. Votre connexion internet
3. Les logs dans le terminal

### Port 8000 déjà utilisé

➡️ Utilisez un autre port :
```bash
uvicorn main:app --reload --port 8080
```

---

## 📚 Documentation complète

- [Description.md](src/Description.md) - Spécifications du projet
- [CLAUDE_SETUP.md](src/CLAUDE_SETUP.md) - Configuration détaillée Claude
- [CHANGES_MARKDOWN.md](src/CHANGES_MARKDOWN.md) - Changements Markdown UI
- [EXAMPLE_AI_RESPONSE.md](src/EXAMPLE_AI_RESPONSE.md) - Exemples réponses IA

---

## 🔐 Sécurité

⚠️ **IMPORTANT** : Ce projet exécute des commandes shell sur votre système !

**Bonnes pratiques :**
- Vérifiez TOUJOURS la commande avant d'appuyer sur Entrée
- Ne faites pas confiance aveuglément à l'IA
- Testez d'abord sur un environnement de test
- Faites attention aux commandes à risque élevé (rouge)

**Ne jamais :**
- Exécuter des commandes sans les comprendre
- Utiliser en production sans validation
- Donner accès à des utilisateurs non formés

---

## 📞 Support

- Issues : [GitHub Issues](https://github.com/votre-repo/ShellIA/issues)
- Documentation API Claude : [docs.anthropic.com](https://docs.anthropic.com)
- Documentation API OpenAI : [platform.openai.com/docs](https://platform.openai.com/docs)

---

**Prêt à démarrer ?** 🚀

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY="votre-clé"
export AI_PROVIDER="claude"
cd src
uvicorn main:app --reload
```

Puis ouvrez http://localhost:8000 et posez votre première question !


**Add google Authentication**

- Aller sur https://console.cloud.google.com/apis/credentials
- Créer un projet si nécessaire
- Configurer l'écran de consentement OAuth (External, ajouter votre email en test user)
- Create Credentials > OAuth client ID > Web application
- Authorized JavaScript origins : http://localhost:8000
- Authorized redirect URIs : http://localhost:8000/login
- Copier le Client ID et l'ajouter au .env

**Add Microsoft Authentication**

https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade
Ou alternativement : https://entra.microsoft.com → Applications → App registrations → New registration

Configuration à faire :

- Name : ShellIA
- Supported account types : Accounts in any organizational directory and personal Microsoft accounts
- Redirect URI : Platform = Web, URI = http://localhost:8000/auth/microsoft/callback
- Cliquer Register
- Copier le Application (client) ID sur la page d'overview
- Aller dans Certificates & secrets → New client secret → copier la Value immédiatement (elle ne sera plus visible après)

**Add Facebook Authentication**
- Aller sur https://developers.facebook.com/apps/create/
  (Si le lien direct ne fonctionne pas : https://developers.facebook.com/ → se connecter → cliquer "My Apps" en haut à droite → bouton vert "Create App")
  Note : si vous ne voyez pas "My Apps", cliquez d'abord sur "Get Started" pour vous inscrire en tant que développeur Meta, acceptez les conditions et vérifiez votre compte.
- Type : choisir "Authenticate and request data from users with Facebook Login" (ou Consumer / Business selon l'interface)
- Nom de l'app : ShellIA
- Ajouter le produit Facebook Login for Web
- Dans Facebook Login → Settings → Valid OAuth Redirect URIs : http://localhost:8000/auth/facebook/callback
- Dans Settings > Basic : copier App ID et App Secret
- Décommenter dans .env :
   - FACEBOOK_APP_ID=votre-app-id
   - FACEBOOK_APP_SECRET=votre-app-secret
