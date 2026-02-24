# 🤖 ShellIA - AI-Powered Shell Copilot

Un copilote shell interactif alimenté par IA (Claude ou ChatGPT) pour l'administration Linux. L'IA suggère des commandes en langage naturel que vous validez avant exécution.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

---

## ✨ Fonctionnalités

- 🗣️ **Langage naturel** : Posez vos questions en français/anglais
- 🤖 **Multi-IA** : Support ChatGPT (OpenAI) et Claude (Anthropic)
- 📝 **Markdown riche** : Réponses formatées et lisibles
- 🎯 **Niveaux de risque** : Commandes colorées (vert/jaune/rouge)
- 🔐 **Sécurité** : Validation explicite avant exécution
- 📊 **Contexte intelligent** : L'IA voit l'historique des commandes
- 💻 **Interface split** : Chat IA + Terminal interactif

---

## 🚀 Démarrage rapide

### Installation

```bash
git clone https://github.com/votre-repo/ShellIA.git
cd ShellIA
pip install -r requirements.txt
```

### Configuration

**Option 1 : Claude (recommandé)**

```bash
export ANTHROPIC_API_KEY="sk-ant-api03-votre-clé"
export AI_PROVIDER="claude"
```

**Option 2 : ChatGPT**

```bash
export OPENAI_API_KEY="sk-votre-clé"
export AI_PROVIDER="chatgpt"
```

### Lancement

```bash
cd src
py -m uvicorn main:app --reload
```

Ouvrez http://localhost:8000 🎉

➡️ **Guide complet** : [QUICKSTART.md](QUICKSTART.md)

---

## 📸 Capture d'écran

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│  🤖 IA Copilot                      │  💻 Terminal                       │
├─────────────────────────────────────┼─────────────────────────────────────┤
│                                     │                                     │
│  Tapez votre question...            │  Prêt à exécuter des commandes...   │
│  ┌────────────────────────────┐     │  ┌────────────────────────────┐     │
│  │ Vérifie l'espace disque    │     │  │ $ df -h                    │     │
│  └────────────────────────────┘     │  │ Filesystem  Size  Used...  │     │
│                                     │  └────────────────────────────┘     │
│  ## Vérification espace disque      │                                     │
│                                     │  ┌────────────────────────────┐     │
│  Je recommande cette commande :     │  │ df -h                      │     │
│                                     │  └────────────────────────────┘     │
│  ┌────────────────────────────┐     │  ▶️ Exécuter (Entrée)              │
│  │ ▶ df -h             [LOW]  │     │                                    │
│  │ Affiche l'espace disque    │     │                                     │
│  └────────────────────────────┘     │                                     │
│                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | 🚀 Guide de démarrage rapide |
| [src/Description.md](src/Description.md) | 📋 Spécifications complètes du projet |
| [CLAUDE_SETUP.md](src/CLAUDE_SETUP.md) | 🤖 Configuration détaillée pour Claude |
| [CHANGES_MARKDOWN.md](src/CHANGES_MARKDOWN.md) | 📝 Implémentation du support Markdown |
| [EXAMPLE_AI_RESPONSE.md](src/EXAMPLE_AI_RESPONSE.md) | 💡 Exemples de réponses IA |

---

## 🏗️ Architecture

```
ShellIA/
├── src/
│   ├── main.py                 # Point d'entrée FastAPI
│   ├── core/
│   │   ├── ai_interface.py     # Interface abstraite AIProvider
│   │   ├── ai_chatgpt.py       # Implémentation ChatGPT
│   │   ├── ai_claude.py        # Implémentation Claude
│   │   ├── shell_executor.py   # Exécuteur de commandes
│   │   └── context_store.py    # Historique des commandes
│   └── ui/
│       └── index.html          # Interface web
├── requirements.txt            # Dépendances Python
├── README.md                   # Ce fichier
└── QUICKSTART.md              # Guide rapide
```

---

## 🎯 Exemples d'utilisation

### Diagnostic système

**Question :** "Vérifie l'utilisation CPU et mémoire"

**Réponse de l'IA :**
```markdown
## Diagnostic CPU et mémoire

Je vais vous proposer plusieurs commandes :

```json
{
  "commands": [
    {
      "cmd": "top -bn1 | head -20",
      "risk": "low",
      "description": "Snapshot des processus actifs"
    },
    {
      "cmd": "free -h",
      "risk": "low",
      "description": "Utilisation de la mémoire"
    }
  ]
}
```

Ces commandes sont sans risque et donnent une vue d'ensemble.
```

### Gestion de services

**Question :** "Le service nginx ne répond plus"

**Réponse de l'IA :**
```markdown
## Diagnostic nginx

Vérifions d'abord l'état :

```json
{
  "commands": [
    {
      "cmd": "systemctl status nginx",
      "risk": "low",
      "description": "Vérifie l'état du service"
    }
  ]
}
```

⚠️ Si le service est arrêté, nous pouvons le redémarrer (risque moyen).
```

---

## 🔐 Sécurité

### Principes de sécurité

✅ **Validation humaine obligatoire** : Aucune commande n'est exécutée automatiquement

✅ **Niveaux de risque visibles** :
- 🟢 **LOW** (vert) : Lecture seule (`ls`, `cat`, `df`)
- 🟡 **MEDIUM** (jaune) : Modifications (`systemctl restart`, `chmod`)
- 🔴 **HIGH** (rouge clignotant) : Danger (`rm -rf`, `reboot`, `dd`)

✅ **Double validation** :
1. Clic sur le bouton → copie la commande
2. Appui sur Entrée → exécute

✅ **Historique complet** : Toutes les commandes sont tracées

### ⚠️ Avertissements

- Ne faites **jamais** confiance aveuglément à l'IA
- Vérifiez **toujours** les commandes avant exécution
- Testez sur un environnement de **test** avant production
- Faites attention aux commandes à **risque élevé**

---

## 🆚 Claude vs ChatGPT

| Critère | ChatGPT (gpt-4o-mini) | Claude (Sonnet 4) |
|---------|----------------------|-------------------|
| **Précision Linux** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Formatage Markdown** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Contexte** | 128k tokens | 200k tokens |
| **Coût** | 💰 Moins cher | 💰💰 Plus cher |
| **Rapidité** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Recommandation :** Claude Sonnet 4 pour la qualité, ChatGPT pour la vitesse/coût.

---

## 🛣️ Roadmap

### ✅ Version actuelle (v1.0)
- [x] Support ChatGPT et Claude
- [x] Interface Markdown riche
- [x] Validation explicite des commandes
- [x] Niveaux de risque colorés
- [x] Contexte intelligent

### 🔜 Prochaines versions

#### v1.1 - Gestion des profils
- [ ] Profils spécialisés (Docker, Proxmox, Rescue)
- [ ] Interface de gestion des profils
- [ ] Sauvegarde/chargement de profils

#### v1.2 - Secrets et SSH
- [ ] Gestion des secrets (mots de passe, clés)
- [ ] Support SSH pour machines distantes
- [ ] Exécution sur containers/VMs

#### v1.3 - Persistance
- [ ] Base de données pour historique
- [ ] Export/import de sessions
- [ ] Recherche dans l'historique

#### v2.0 - Avancé
- [ ] Terminal interactif complet (xterm.js)
- [ ] Multi-utilisateurs
- [ ] Whitelist/blacklist de commandes
- [ ] Monitoring en temps réel

---

## 🤝 Contribution

Les contributions sont bienvenues ! Voici comment contribuer :

1. **Fork** le projet
2. **Créez une branche** : `git checkout -b feature/AmazingFeature`
3. **Committez** : `git commit -m 'Add AmazingFeature'`
4. **Push** : `git push origin feature/AmazingFeature`
5. **Ouvrez une Pull Request**

### Idées de contribution

- 🐛 Correction de bugs
- ✨ Nouvelles fonctionnalités
- 📝 Amélioration de la documentation
- 🌍 Traductions
- 🎨 Amélioration de l'UI

---

## 📄 License

Ce projet est sous licence MIT. Voir [LICENSE](LICENSE) pour plus de détails.

---

## 🙏 Remerciements

- [Anthropic](https://www.anthropic.com) pour Claude
- [OpenAI](https://openai.com) pour ChatGPT
- [FastAPI](https://fastapi.tiangolo.com) pour le framework web
- [marked.js](https://marked.js.org) pour le parsing Markdown

---

## 📞 Support & Contact

- 🐛 **Issues** : [GitHub Issues](https://github.com/votre-repo/ShellIA/issues)
- 💬 **Discussions** : [GitHub Discussions](https://github.com/votre-repo/ShellIA/discussions)
- 📧 **Email** : votre-email@example.com

---

## ⭐ Star History

Si ce projet vous aide, n'hésitez pas à lui donner une ⭐ sur GitHub !

---

**Made with ❤️ for SysAdmins**

*ShellIA - Votre copilote intelligent pour le shell Linux*
