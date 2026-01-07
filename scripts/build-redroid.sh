#!/bin/bash
# Build custom redroid image with fingerprint injection support

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "Building MobileDroid custom redroid image..."

# Check if base image exists
if ! docker image inspect redroid/redroid:14.0.0_64only-latest &> /dev/null; then
    echo "Pulling base redroid image..."
    docker pull redroid/redroid:14.0.0_64only-latest
fi

# Build custom image
cd "$PROJECT_ROOT/docker"
docker build \
    -t mobiledroid/redroid-custom:latest \
    -f Dockerfile.redroid-custom \
    .

echo "Successfully built mobiledroid/redroid-custom:latest"
