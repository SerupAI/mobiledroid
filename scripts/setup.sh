#!/bin/bash
# MobileDroid Setup Script
# This script sets up the development environment

set -e

echo "============================================"
echo "       MobileDroid Setup Script            "
echo "============================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "\n${YELLOW}Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi
echo -e "${GREEN}✓ Docker is installed${NC}"

# Check Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Docker Compose is installed${NC}"

# Check if running on Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "\n${YELLOW}Checking kernel modules for redroid...${NC}"

    # Check for required kernel modules
    if ! lsmod | grep -q binder_linux; then
        echo -e "${YELLOW}binder_linux module not loaded. Attempting to load...${NC}"
        sudo modprobe binder_linux devices="binder,hwbinder,vndbinder" || {
            echo -e "${RED}Failed to load binder_linux module${NC}"
            echo "You may need to install it: https://github.com/nickel8448/binder_linux"
        }
    fi

    if ! lsmod | grep -q ashmem_linux; then
        echo -e "${YELLOW}ashmem_linux module not loaded. Attempting to load...${NC}"
        sudo modprobe ashmem_linux || {
            echo -e "${YELLOW}ashmem_linux not available (optional on newer kernels)${NC}"
        }
    fi

    echo -e "${GREEN}✓ Kernel modules checked${NC}"
else
    echo -e "${YELLOW}Note: redroid requires a Linux host with kernel modules.${NC}"
    echo "On macOS/Windows, you'll need a Linux VM to run device containers."
fi

# Setup environment file
echo -e "\n${YELLOW}Setting up environment...${NC}"
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file from .env.example${NC}"
    echo -e "${YELLOW}Please edit .env and add your API keys${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Create data directories
echo -e "\n${YELLOW}Creating data directories...${NC}"
mkdir -p docker/data
mkdir -p packages/api/data
echo -e "${GREEN}✓ Data directories created${NC}"

# Build custom redroid image
echo -e "\n${YELLOW}Building custom redroid image...${NC}"
cd docker
docker build -t mobiledroid/redroid-custom:latest -f Dockerfile.redroid-custom . || {
    echo -e "${YELLOW}Note: redroid image build may fail if base image is not available${NC}"
    echo "You can pull it manually: docker pull redroid/redroid:14.0.0_64only-latest"
}
cd ..

# Install Python dependencies
echo -e "\n${YELLOW}Setting up Python environment for API...${NC}"
if command -v python3 &> /dev/null; then
    cd packages/api
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo -e "${GREEN}✓ Created Python virtual environment${NC}"
    fi
    source venv/bin/activate
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓ Installed API dependencies${NC}"
    deactivate
    cd ../..
fi

# Install Node.js dependencies for UI
echo -e "\n${YELLOW}Setting up Node.js environment for UI...${NC}"
if command -v npm &> /dev/null; then
    cd packages/ui
    npm install --silent
    echo -e "${GREEN}✓ Installed UI dependencies${NC}"
    cd ../..
fi

# Done
echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}       Setup Complete!                      ${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your ANTHROPIC_API_KEY"
echo "2. Update DOCKER_HOST_IP in .env to your Docker host (default: 192.168.1.26)"
echo "3. Start the platform:"
echo "   docker-compose -f docker/docker-compose.yml up -d"
echo ""
echo "4. Access the services (default ports):"
echo "   UI:       http://<docker-host>:3100"
echo "   API docs: http://<docker-host>:8100/docs"
echo ""
echo "For development mode with hot-reload:"
echo "   docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up"
