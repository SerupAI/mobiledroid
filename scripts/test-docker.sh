#!/bin/bash
# Test Docker builds locally
# Usage: ./scripts/test-docker.sh [--full]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "=== MobileDroid Docker Build Test ==="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() { echo -e "${GREEN}✓ $1${NC}"; }
error() { echo -e "${RED}✗ $1${NC}"; }
info() { echo -e "${YELLOW}→ $1${NC}"; }

# Check if --full flag is passed (runs full compose up)
FULL_TEST=false
if [[ "$1" == "--full" ]]; then
    FULL_TEST=true
fi

# Test 1: Build API Dockerfile
info "Building API image..."
if docker build -f docker/Dockerfile.api -t mobiledroid/api:test \
    --build-arg GIT_COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
    . > /dev/null 2>&1; then
    success "API image built successfully"
else
    error "API image build failed"
    docker build -f docker/Dockerfile.api -t mobiledroid/api:test .
    exit 1
fi

# Test 2: Build UI Dockerfile
info "Building UI image..."
if docker build -f docker/Dockerfile.ui -t mobiledroid/ui:test \
    --build-arg GIT_COMMIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown") \
    --build-arg NEXT_PUBLIC_API_URL=http://localhost:8100 \
    . > /dev/null 2>&1; then
    success "UI image built successfully"
else
    error "UI image build failed"
    docker build -f docker/Dockerfile.ui -t mobiledroid/ui:test .
    exit 1
fi

# Test 3: Build test Dockerfile
info "Building test image..."
if docker build -f docker/Dockerfile.test -t mobiledroid/test:latest . > /dev/null 2>&1; then
    success "Test image built successfully"
else
    error "Test image build failed"
    docker build -f docker/Dockerfile.test -t mobiledroid/test:latest .
    exit 1
fi

# Test 4: Run unit tests in Docker
info "Running unit tests in Docker..."
if docker run --rm mobiledroid/test:latest pytest tests/unit -v --tb=short; then
    success "Unit tests passed"
else
    error "Unit tests failed"
    exit 1
fi

# Full test: Start docker compose and verify health
if $FULL_TEST; then
    echo ""
    info "Starting full Docker Compose test..."

    cd docker

    # Start services
    docker compose up -d --build

    # Wait for services to be healthy
    info "Waiting for services to start..."
    sleep 10

    # Check API health
    if curl -sf http://localhost:8100/health > /dev/null 2>&1; then
        success "API health check passed"
    else
        error "API health check failed"
        docker compose logs api
        docker compose down
        exit 1
    fi

    # Check UI
    if curl -sf http://localhost:3100 > /dev/null 2>&1; then
        success "UI health check passed"
    else
        error "UI health check failed"
        docker compose logs ui
        docker compose down
        exit 1
    fi

    # Cleanup
    info "Cleaning up..."
    docker compose down

    success "Full Docker Compose test passed!"
fi

echo ""
echo "=== All Docker tests passed! ==="
echo ""
echo "Images built:"
echo "  - mobiledroid/api:test"
echo "  - mobiledroid/ui:test"
echo "  - mobiledroid/test:latest"
echo ""
if ! $FULL_TEST; then
    echo "Run with --full flag to also test Docker Compose startup"
fi
