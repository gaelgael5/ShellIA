#!/bin/bash
# ============================================================
# ShellIA - Docker Entrypoint
# ============================================================
set -e

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║          ShellIA - AI Shell Copilot              ║"
echo "╚══════════════════════════════════════════════════╝"
echo ""
echo "  Environment : ${SHELLIA_ENV:-local}"
echo "  TZ          : ${TZ:-UTC}"
echo "  Port        : 8000"
echo ""

# Fix volume permissions (volumes may be mounted as root)
# Run as root first, then drop privileges
if [ "$(id -u)" = "0" ]; then
    mkdir -p /app/users /app/environments /app/data
    chown -R shellia:shellia /app/users /app/environments /app/data 2>/dev/null || true
    exec gosu shellia "$0" "$@"
fi

# Ensure directories exist
mkdir -p /app/users /app/environments /app/data

# Warn if SECRET_KEY is not set
if [ -z "$SECRET_KEY" ]; then
    echo "  ⚠️  SECRET_KEY not set — a random key will be generated"
    echo "     Sessions will not persist across container restarts"
    echo "     Set SECRET_KEY for production: openssl rand -hex 32"
    echo ""
fi

echo "▶ Starting ShellIA..."
echo ""

cd /app/src

exec python3 -m uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 1 \
    --log-level info
