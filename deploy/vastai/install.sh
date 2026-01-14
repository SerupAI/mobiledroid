#!/bin/bash
#
# MobileDroid Installation Script for Vast.ai GPU
#
# Usage:
#   1. Rent a GPU instance on Vast.ai
#   2. SSH into your instance
#   3. Run: curl -fsSL https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/vastai/install.sh | bash
#
# Recommended Instance Types:
#   - RTX 4090 (24GB) - Best performance, ~$0.34/hr
#   - RTX 3090 (24GB) - Great value, ~$0.20-0.30/hr
#   - A100 (40/80GB) - Enterprise workloads
#
# Requirements:
#   - Docker image or instance with Docker installed
#   - 50GB+ disk space
#   - Ports 3100 and 8100 available
#

set -e

echo "=========================================="
echo "  MobileDroid GPU Installation"
echo "  Vast.ai"
echo "=========================================="

# Vast.ai typically uses /root or /workspace
WORKSPACE="${WORKSPACE:-/root}"
INSTALL_DIR="${WORKSPACE}/mobiledroid"

echo ""
echo "[1/5] Checking environment..."

# Check for GPU
if command -v nvidia-smi &> /dev/null; then
    echo "GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "WARNING: No GPU detected. GPU acceleration will not be available."
fi

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo ""
    echo "[2/5] Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    systemctl start docker || service docker start || true
else
    echo ""
    echo "[2/5] Docker already installed"
fi

# Install Docker Compose if not present
if ! docker compose version &> /dev/null; then
    echo ""
    echo "[3/5] Installing Docker Compose..."
    apt-get update && apt-get install -y docker-compose-plugin || {
        # Fallback to standalone docker-compose
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    }
else
    echo ""
    echo "[3/5] Docker Compose already installed"
fi

echo ""
echo "[4/5] Cloning MobileDroid..."
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull
else
    git clone https://github.com/serup-ai/mobiledroid.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""
echo "[5/5] Configuring and starting services..."

# Create .env file with GPU mode enabled
cat > "$INSTALL_DIR/.env" << EOF
# MobileDroid Configuration (Vast.ai GPU)
ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-}
DATABASE_URL=postgresql+asyncpg://mobiledroid:mobiledroid@db:5432/mobiledroid
REDIS_URL=redis://redis:6379
API_HOST=0.0.0.0
API_PORT=8100
DOCKER_NETWORK=mobiledroid_network
DEBUG=false
# GPU acceleration enabled
REDROID_GPU_MODE=host
EOF

# Start services with GPU support
cd "$INSTALL_DIR/docker"
docker compose up -d || docker-compose up -d

# Get public IP
PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')

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
    echo "  Edit ${INSTALL_DIR}/.env and restart:"
    echo "    cd ${INSTALL_DIR}/docker && docker compose restart"
    echo ""
fi
echo "  GPU Status: nvidia-smi"
echo "  Logs: docker compose -f ${INSTALL_DIR}/docker/docker-compose.yml logs -f"
echo ""
echo "  IMPORTANT: Make sure ports 3100 and 8100 are open in your Vast.ai instance!"
echo ""
