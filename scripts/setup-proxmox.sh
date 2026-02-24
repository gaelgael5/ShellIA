#!/bin/bash
# ============================================================
# ShellIA — Proxmox LXC Setup Script
# ============================================================
# Installs Docker, Portainer, ShellIA and optionally Watchtower
# Tested on: Ubuntu 22.04 LXC (Proxmox)
#
# Usage:
#   chmod +x setup-proxmox.sh
#   sudo ./setup-proxmox.sh
# ============================================================

set -e

# ── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# ── Helpers ──────────────────────────────────────────────────
info()    { echo -e "${CYAN}  ℹ  $*${NC}"; }
success() { echo -e "${GREEN}  ✅  $*${NC}"; }
warning() { echo -e "${YELLOW}  ⚠️   $*${NC}"; }
error()   { echo -e "${RED}  ❌  $*${NC}"; exit 1; }
header()  { echo -e "\n${WHITE}══════════════════════════════════════════════${NC}"; echo -e "${WHITE}  $*${NC}"; echo -e "${WHITE}══════════════════════════════════════════════${NC}\n"; }

ask_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    local answer
    if [ "$default" = "y" ]; then
        read -rp "$(echo -e "${YELLOW}  ? $prompt [Y/n]: ${NC}")" answer
        answer="${answer:-y}"
    else
        read -rp "$(echo -e "${YELLOW}  ? $prompt [y/N]: ${NC}")" answer
        answer="${answer:-n}"
    fi
    [[ "$answer" =~ ^[Yy]$ ]]
}

# ── Banner ───────────────────────────────────────────────────
echo ""
echo -e "${BLUE}  ███████╗██╗  ██╗███████╗██╗     ██╗     ██╗ █████╗ ${NC}"
echo -e "${BLUE}  ██╔════╝██║  ██║██╔════╝██║     ██║     ██║██╔══██╗${NC}"
echo -e "${BLUE}  ███████╗███████║█████╗  ██║     ██║     ██║███████║${NC}"
echo -e "${BLUE}  ╚════██║██╔══██║██╔══╝  ██║     ██║     ██║██╔══██║${NC}"
echo -e "${BLUE}  ███████║██║  ██║███████╗███████╗███████╗██║██║  ██║${NC}"
echo -e "${BLUE}  ╚══════╝╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝╚═╝╚═╝  ╚═╝${NC}"
echo ""
echo -e "${WHITE}  Proxmox LXC Setup Script${NC}"
echo -e "${CYAN}  Installs Docker, Portainer, ShellIA and Watchtower${NC}"
echo ""

# ── Root check ───────────────────────────────────────────────
if [ "$(id -u)" -ne 0 ]; then
    error "This script must be run as root. Use: sudo ./setup-proxmox.sh"
fi

# ── OS check ─────────────────────────────────────────────────
if ! grep -qiE "ubuntu|debian" /etc/os-release 2>/dev/null; then
    warning "This script is designed for Ubuntu/Debian. Proceeding anyway..."
fi

# ── Install dir ──────────────────────────────────────────────
INSTALL_DIR="/opt/shellia"
SHELLIA_PORT="${SHELLIA_PORT:-8000}"
PORTAINER_PORT="${PORTAINER_PORT:-9000}"

# ============================================================
# STEP 1 — Docker
# ============================================================
header "Step 1 — Docker"

if command -v docker &>/dev/null; then
    success "Docker already installed ($(docker --version))"
else
    info "Installing Docker CE..."

    apt-get update -q
    apt-get install -yq ca-certificates curl gnupg lsb-release

    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
        | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    chmod a+r /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
      | tee /etc/apt/sources.list.d/docker.list > /dev/null

    apt-get update -q
    apt-get install -yq docker-ce docker-ce-cli containerd.io docker-compose-plugin

    systemctl enable --now docker
    success "Docker installed successfully"
fi

# ============================================================
# STEP 2 — Portainer
# ============================================================
header "Step 2 — Portainer"

if docker ps -a --format '{{.Names}}' | grep -q "^portainer$"; then
    success "Portainer already running"
else
    info "Installing Portainer CE (port ${PORTAINER_PORT})..."

    docker volume create portainer_data 2>/dev/null || true

    docker run -d \
        --name portainer \
        --restart unless-stopped \
        -p "${PORTAINER_PORT}:9000" \
        -p 9443:9443 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v portainer_data:/data \
        portainer/portainer-ce:latest

    success "Portainer installed — http://$(hostname -I | awk '{print $1}'):${PORTAINER_PORT}"
fi

# ============================================================
# STEP 3 — Watchtower (optional)
# ============================================================
header "Step 3 — Watchtower (auto-update)"

echo -e "  ${CYAN}Watchtower automatically pulls and restarts containers${NC}"
echo -e "  ${CYAN}when a new Docker image is published on Docker Hub.${NC}"
echo ""

INSTALL_WATCHTOWER=false
if ask_yes_no "Install Watchtower to auto-update ShellIA?"; then
    INSTALL_WATCHTOWER=true

    if docker ps -a --format '{{.Names}}' | grep -q "^shellia_watchtower$"; then
        success "Watchtower already running"
    else
        info "Installing Watchtower (checks for updates every hour)..."

        docker run -d \
            --name shellia_watchtower \
            --restart unless-stopped \
            -v /var/run/docker.sock:/var/run/docker.sock \
            containrrr/watchtower:latest \
            --cleanup \
            --interval 3600 \
            shellia

        success "Watchtower installed — will auto-update ShellIA every hour"
    fi
else
    info "Watchtower skipped. You can update ShellIA manually with:"
    echo -e "       ${YELLOW}cd ${INSTALL_DIR} && docker compose pull && docker compose up -d${NC}"
fi

# ============================================================
# STEP 4 — ShellIA
# ============================================================
header "Step 4 — ShellIA"

mkdir -p "${INSTALL_DIR}"
cd "${INSTALL_DIR}"

# Download docker-compose.yml if not present
if [ ! -f docker-compose.yml ]; then
    info "Downloading docker-compose.yml..."
    curl -fsSL https://raw.githubusercontent.com/gaelgael5/ShellIA/main/docker-compose.yml \
        -o docker-compose.yml
fi

# Download .env.docker if not present
if [ ! -f .env ]; then
    info "Downloading environment template..."
    curl -fsSL https://raw.githubusercontent.com/gaelgael5/ShellIA/main/.env.docker \
        -o .env

    # Generate a random SECRET_KEY
    SECRET_KEY=$(openssl rand -hex 32)
    sed -i "s|SECRET_KEY=.*|SECRET_KEY=${SECRET_KEY}|" .env

    # Set port if customized
    if [ "${SHELLIA_PORT}" != "8000" ]; then
        sed -i "s|SHELLIA_PORT=.*|SHELLIA_PORT=${SHELLIA_PORT}|" .env
    fi

    success "Generated SECRET_KEY and saved to .env"
fi

info "Pulling ShellIA image..."
docker compose pull

info "Starting ShellIA..."
docker compose up -d

success "ShellIA started — http://$(hostname -I | awk '{print $1}'):${SHELLIA_PORT}"

# ============================================================
# SUMMARY
# ============================================================
header "✅ Installation complete"

LOCAL_IP=$(hostname -I | awk '{print $1}')

echo -e "  ${GREEN}ShellIA${NC}     →  http://${LOCAL_IP}:${SHELLIA_PORT}"
echo -e "  ${GREEN}Portainer${NC}   →  http://${LOCAL_IP}:${PORTAINER_PORT}"
if [ "$INSTALL_WATCHTOWER" = true ]; then
    echo -e "  ${GREEN}Watchtower${NC}  →  auto-update every hour (${YELLOW}docker logs shellia_watchtower${NC})"
else
    echo -e "  ${YELLOW}Watchtower${NC}  →  not installed (manual update: ${YELLOW}cd ${INSTALL_DIR} && docker compose pull && docker compose up -d${NC})"
fi

echo ""
echo -e "  ${CYAN}Config files:${NC}  ${INSTALL_DIR}/.env"
echo -e "  ${CYAN}Logs:${NC}          docker compose -f ${INSTALL_DIR}/docker-compose.yml logs -f"
echo ""
echo -e "${WHITE}  Happy shelling! 🚀${NC}"
echo ""
