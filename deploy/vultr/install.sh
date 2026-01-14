#!/bin/bash
#
# MobileDroid Installation Script for Vultr
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/vultr/install.sh | bash
#
# Or download and run with API key:
#   curl -O https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/vultr/install.sh
#   chmod +x install.sh
#   ANTHROPIC_API_KEY=sk-ant-xxx ./install.sh
#
# Requirements:
#   - Ubuntu 22.04 Instance
#   - Minimum: 2 vCPU, 4GB RAM
#   - Recommended: 4 vCPU, 8GB RAM (High Frequency)
#

set -e

echo "=========================================="
echo "  MobileDroid Installation"
echo "  Vultr Instance"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root (sudo)"
    exit 1
fi

# Log output
exec > >(tee /var/log/mobiledroid-install.log) 2>&1

echo ""
echo "[1/6] Updating system..."
apt-get update
apt-get upgrade -y

echo ""
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "Docker already installed"
fi

echo ""
echo "[3/6] Installing Docker Compose..."
apt-get install -y docker-compose-plugin

echo ""
echo "[4/6] Loading kernel modules for Android containers..."
modprobe binder_linux devices="binder,hwbinder,vndbinder" 2>/dev/null || echo "binder_linux not available (may work without)"
modprobe ashmem_linux 2>/dev/null || echo "ashmem_linux not available (may work without)"

# Persist modules
grep -q "binder_linux" /etc/modules || echo "binder_linux" >> /etc/modules
grep -q "ashmem_linux" /etc/modules || echo "ashmem_linux" >> /etc/modules

echo ""
echo "[5/6] Cloning MobileDroid..."
if [ -d "/opt/mobiledroid" ]; then
    echo "Updating existing installation..."
    cd /opt/mobiledroid
    git pull
else
    git clone https://github.com/serup-ai/mobiledroid.git /opt/mobiledroid
    cd /opt/mobiledroid
fi

echo ""
echo "[6/6] Configuring and starting services..."

# Create .env file
cat > /opt/mobiledroid/.env << EOF
# MobileDroid Configuration
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
DATABASE_URL=postgresql+asyncpg://mobiledroid:mobiledroid@db:5432/mobiledroid
REDIS_URL=redis://redis:6379
API_HOST=0.0.0.0
API_PORT=8100
DOCKER_NETWORK=mobiledroid_network
DEBUG=false
EOF

# Start services
cd /opt/mobiledroid/docker
docker compose up -d

# Get public IP (Vultr metadata or fallback)
PUBLIC_IP=$(curl -s http://169.254.169.254/v1/interfaces/0/ipv4/address 2>/dev/null || hostname -I | awk '{print $1}')

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "  Web UI:   http://${PUBLIC_IP}:3100"
echo "  API:      http://${PUBLIC_IP}:8100"
echo "  API Docs: http://${PUBLIC_IP}:8100/docs"
echo ""
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "  NOTE: No ANTHROPIC_API_KEY set."
    echo "  Edit /opt/mobiledroid/.env and restart:"
    echo "    cd /opt/mobiledroid/docker && docker compose restart"
    echo ""
fi
echo "  Logs: docker compose -f /opt/mobiledroid/docker/docker-compose.yml logs -f"
echo ""
