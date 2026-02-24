#!/bin/bash
# ============================================================
# ShellIA - Entrypoint Docker
# ============================================================
set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║          ShellIA - AI Shell Copilot              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Environnement : ${SHELLIA_ENV:-local}"
echo "  TZ            : ${TZ:-UTC}"
echo "  Port          : 8000"
echo ""

# Vérifier que les répertoires de données existent
mkdir -p /app/users /app/environments

echo "▶ Démarrage de ShellIA..."
echo ""

cd /app/src

exec python3 -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
