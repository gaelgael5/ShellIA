# 🤖 ShellIA - AI-Powered Shell Copilot

An interactive AI shell copilot (powered by Claude or ChatGPT) for Linux administration. The AI suggests commands in natural language that you validate before execution.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.8+-green)
![License](https://img.shields.io/badge/license-MIT-orange)
[![Docker](https://img.shields.io/badge/docker-blackbeardteam%2Fshellia-blue?logo=docker)](https://hub.docker.com/r/blackbeardteam/shellia)
[![AppVeyor](https://ci.appveyor.com/api/projects/status/github/gaelgael5/ShellIA?branch=main&svg=true)](https://ci.appveyor.com/project/gaelgael5/shellia)

---

## ✨ Features

- 🗣️ **Natural language** : Ask questions in English or French
- 🤖 **Multi-AI** : Supports ChatGPT (OpenAI) and Claude (Anthropic)
- 📝 **Rich Markdown** : Formatted and readable responses
- 🎯 **Risk levels** : Color-coded commands (green/yellow/red)
- 🔐 **Security** : Explicit validation before execution
- 📊 **Smart context** : AI sees command history
- 💬 **AI Profiles** : Inject context per session (e.g. "I am on Proxmox")
- 💻 **Split interface** : AI Chat + Interactive Terminal

---

## 🚀 Quick Start

### 🐳 Docker (recommended)

**Option 1 — Docker run**

```bash
docker run -d \
  --name shellia \
  -p 8000:8000 \
  -e SECRET_KEY=your-secret-key-here \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  -e AI_PROVIDER=claude \
  -v shellia_data:/app/data \
  -v shellia_users:/app/users \
  --restart unless-stopped \
  blackbeardteam/shellia:latest
```

Then open http://localhost:8000 🎉

**Option 2 — Docker Compose**

```bash
# Clone the repo
git clone https://github.com/gaelgael5/ShellIA.git
cd ShellIA

# Configure environment
cp .env.docker .env
# Edit .env with your API keys and a strong SECRET_KEY

# Start
docker compose up -d

# View logs
docker compose logs -f
```

Then open http://localhost:8000 🎉

**Useful Docker commands:**

```bash
# Stop
docker compose down

# Rebuild after update
docker compose up -d --build

# View logs
docker compose logs -f shellia

# Remove containers but keep data
docker compose down
# (volumes shellia_data and shellia_users are preserved)
```

### 🐍 Local (Python)

```bash
git clone https://github.com/gaelgael5/ShellIA.git
cd ShellIA
pip install -r requirements.txt
```

**Configure your AI provider:**

```bash
# Option 1: Claude (recommended)
export ANTHROPIC_API_KEY="sk-ant-api03-your-key"
export AI_PROVIDER="claude"

# Option 2: ChatGPT
export OPENAI_API_KEY="sk-your-key"
export AI_PROVIDER="chatgpt"
```

**Launch:**

```bash
cd src
python -m uvicorn main:app --reload
```

Open http://localhost:8000 🎉

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | ✅ | — | JWT secret key (use a strong random value) |
| `AI_PROVIDER` | ❌ | `claude` | AI provider: `claude` or `chatgpt` |
| `ANTHROPIC_API_KEY` | ❌ | — | Claude API key |
| `OPENAI_API_KEY` | ❌ | — | OpenAI API key |
| `CLAUDE_MODEL` | ❌ | `claude-sonnet-4-20250514` | Claude model to use |
| `SHELLIA_ENV` | ❌ | `local` | Execution environment |
| `TZ` | ❌ | `Europe/Paris` | Timezone |
| `SHELLIA_PORT` | ❌ | `8000` | Exposed port (docker compose only) |

> 💡 API keys can also be configured directly in the web interface (Settings → APIs).
### 🔑 About SECRET_KEY

`SECRET_KEY` is used to **sign and verify JWT tokens** for user authentication.

- When you log in, ShellIA generates a JWT token signed with this key
- On every subsequent request, it verifies the token has not been tampered with
- Without the correct `SECRET_KEY`, no one can forge a valid authentication token

**Generate a strong key:**
```bash
openssl rand -hex 32
```

> ⚠️ **Keep it secret.** Never commit it to your repository — use `.env` or Docker secrets instead.



---

## 📸 Screenshot

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│  🤖 AI Copilot                      │  💻 Terminal                        │
├─────────────────────────────────────┼─────────────────────────────────────┤
│                                     │                                     │
│  Ask your question...               │  Ready to execute commands...       │
│  ┌────────────────────────────┐     │  ┌────────────────────────────┐     │
│  │ Check disk space           │     │  │ $ df -h                    │     │
│  └────────────────────────────┘     │  │ Filesystem  Size  Used...  │     │
│                                     │  └────────────────────────────┘     │
│  ## Disk space check                │                                     │
│                                     │  ┌────────────────────────────┐     │
│  I recommend this command:          │  │ df -h                      │     │
│                                     │  └────────────────────────────┘     │
│  ┌────────────────────────────┐     │  ▶️ Execute (Enter)                 │
│  │ ▶ df -h             [LOW]  │     │                                     │
│  │ Shows disk usage           │     │                                     │
│  └────────────────────────────┘     │                                     │
│                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

---

## 🏗️ Architecture

```
ShellIA/
├── src/
│   ├── main.py                 # FastAPI entry point
│   ├── core/
│   │   ├── ai_interface.py     # Abstract AIProvider interface
│   │   ├── ai_chatgpt.py       # ChatGPT implementation
│   │   ├── ai_claude.py        # Claude implementation
│   │   ├── shell_executor.py   # Command executor (local)
│   │   ├── ssh_executor.py     # Command executor (SSH)
│   │   ├── context_store.py    # Command + conversation history
│   │   └── profile_manager.py  # AI context profiles
│   └── ui/
│       └── index.html          # Web interface
├── docker/
│   └── entrypoint.sh           # Docker startup script
├── Dockerfile                  # Ubuntu 22.04 based image
├── docker-compose.yml          # Docker Compose configuration
├── .env.docker                 # Environment variables template
├── appveyor.yml                # CI/CD configuration
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🎯 Usage Examples

### System diagnostics

**Question:** "Check CPU and memory usage"

**AI response:**
```markdown
## CPU and Memory Diagnostic

Here are the recommended commands:

{
  "commands": [
    {
      "cmd": "top -bn1 | head -20",
      "risk": "low",
      "description": "Snapshot of active processes"
    },
    {
      "cmd": "free -h",
      "risk": "low",
      "description": "Memory usage overview"
    }
  ]
}
```

### Service management

**Question:** "nginx is not responding"

**AI response:**
```markdown
## Nginx Diagnostic

Let's check the service status first:

{
  "commands": [
    {
      "cmd": "systemctl status nginx",
      "risk": "low",
      "description": "Check service status"
    }
  ]
}

⚠️ If the service is stopped, we can restart it (medium risk).
```

---

## 🔐 Security

### Principles

✅ **Mandatory human validation** : No command is executed automatically

✅ **Visible risk levels** :
- 🟢 **LOW** (green) : Read-only (`ls`, `cat`, `df`)
- 🟡 **MEDIUM** (yellow) : Modifications (`systemctl restart`, `chmod`)
- 🔴 **HIGH** (red/blinking) : Dangerous (`rm -rf`, `reboot`, `dd`)

✅ **Two actions on commands** :
- ▶️ **Execute button** → sends command to terminal and runs it
- 📋 **Copy button** → inserts command in terminal without running

✅ **Full audit trail** : All commands are tracked

### ⚠️ Warnings

- **Never** blindly trust AI suggestions
- **Always** verify commands before execution
- Test on a **staging** environment before production
- Pay special attention to **high-risk** commands

---

## 🆚 Claude vs ChatGPT

| Criteria | ChatGPT (gpt-4o-mini) | Claude (Sonnet 4) |
|----------|----------------------|-------------------|
| **Linux accuracy** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Markdown formatting** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Context window** | 128k tokens | 200k tokens |
| **Cost** | 💰 Cheaper | 💰💰 More expensive |
| **Speed** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

**Recommendation:** Claude Sonnet 4 for quality, ChatGPT for speed/cost.

---

## 🛣️ Roadmap

### ✅ Current version (v1.0)
- [x] ChatGPT and Claude support
- [x] Rich Markdown interface
- [x] Explicit command validation
- [x] Color-coded risk levels
- [x] Smart conversation history
- [x] AI context profiles
- [x] Docker support
- [x] CI/CD with AppVeyor

### 🔜 Upcoming versions

#### v1.1
- [ ] Specialized profiles (Docker, Proxmox, Rescue mode)
- [ ] WebSocket terminal for real interactive SSH

#### v1.2
- [ ] Secret management (passwords, keys)
- [ ] Full interactive terminal (xterm.js)

#### v2.0
- [ ] Multi-user support
- [ ] Command whitelist/blacklist
- [ ] Real-time monitoring

---

## 🤝 Contributing

Contributions are welcome!

1. **Fork** the project
2. **Create a branch** : `git checkout -b feature/AmazingFeature`
3. **Commit** : `git commit -m 'Add AmazingFeature'`
4. **Push** : `git push origin feature/AmazingFeature`
5. **Open a Pull Request**

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Anthropic](https://www.anthropic.com) for Claude
- [OpenAI](https://openai.com) for ChatGPT
- [FastAPI](https://fastapi.tiangolo.com) for the web framework
- [marked.js](https://marked.js.org) for Markdown parsing

---

**Made with ❤️ for SysAdmins**

*ShellIA — Your intelligent Linux shell copilot*
