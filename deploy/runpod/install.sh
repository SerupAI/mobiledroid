#!/bin/bash
#
# MobileDroid Installation Script for RunPod GPU
#
# Usage:
#   1. Create a RunPod pod with Ubuntu + Docker template
#   2. SSH into your pod
#   3. Run: curl -fsSL https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/runpod/install.sh | bash
#
# Recommended Templates:
#   - RunPod Pytorch (has Docker pre-installed)
#   - Ubuntu 22.04 + Docker
#
# Recommended GPUs:
#   - RTX 3090 (24GB) - Best value at $0.22-0.43/hr
#   - RTX 4090 (24GB) - Premium performance
#   - A100 (40/80GB) - Enterprise workloads
#

set -e

echo "=========================================="
echo "  MobileDroid GPU Installation"
echo "  RunPod"
echo "=========================================="

# Detect workspace directory (RunPod uses /workspace)
WORKSPACE="${WORKSPACE:-/workspace}"
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
else
    echo ""
    echo "[2/5] Docker already installed"
fi

# Install Docker Compose if not present
if ! docker compose version &> /dev/null; then
    echo ""
    echo "[3/5] Installing Docker Compose..."
    apt-get update && apt-get install -y docker-compose-plugin
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
# MobileDroid Configuration (RunPod GPU)
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
docker compose up -d

# Get public IP (RunPod provides this via environment)
PUBLIC_IP="${RUNPOD_PUBLIC_IP:-$(hostname -I | awk '{print $1}')}"
PUBLIC_PORT="${RUNPOD_TCP_PORT_3100:-3100}"
API_PORT="${RUNPOD_TCP_PORT_8100:-8100}"

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "  Web UI:   http://${PUBLIC_IP}:${PUBLIC_PORT}"
echo "  API:      http://${PUBLIC_IP}:${API_PORT}"
echo "  API Docs: http://${PUBLIC_IP}:${API_PORT}/docs"
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
