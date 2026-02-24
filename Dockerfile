# ============================================================
# ShellIA - Dockerfile (Ubuntu 22.04 LTS)
# ============================================================
FROM ubuntu:22.04

LABEL maintainer="gaelgael5"
LABEL description="ShellIA - AI-Powered Shell Copilot"
LABEL version="1.0.0"

# ── Variables d'environnement de build ──────────────────────
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Europe/Paris

# ── Dépendances système ──────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    python3-dev \
    bash \
    curl \
    wget \
    openssh-client \
    git \
    ca-certificates \
    tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# ── Alias python3 → python ──────────────────────────────────
RUN ln -sf /usr/bin/python3.11 /usr/bin/python3 \
    && ln -sf /usr/bin/python3 /usr/bin/python

# ── Répertoire de travail ────────────────────────────────────
WORKDIR /app

# ── Dépendances Python (cachée séparément pour le rebuild) ──
COPY requirements.txt .
RUN pip3 install --no-cache-dir --upgrade pip \
    && pip3 install --no-cache-dir -r requirements.txt

# ── Code source ──────────────────────────────────────────────
COPY src/ ./src/

# ── Script d'entrée ──────────────────────────────────────────
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ── Répertoires de données (montés en volume en prod) ────────
RUN mkdir -p /app/users /app/environments /app/data

# ── Utilisateur non-root pour la sécurité ───────────────────
RUN groupadd -r shellia && useradd -r -g shellia -s /bin/bash shellia \
    && chown -R shellia:shellia /app

USER shellia

# ── Port exposé ──────────────────────────────────────────────
EXPOSE 8000

# ── Healthcheck ──────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/auth/config || exit 1

# ── Démarrage ────────────────────────────────────────────────
ENTRYPOINT ["/entrypoint.sh"]
