#!/bin/bash

# Test script for local Docker host (192.168.1.26)
# Usage: ./test-local.sh [--api] [--ui] [--no-cache]

set -e

# Parse arguments
NO_CACHE=false
TEST_API=true
TEST_UI=true
EXPLICIT_SERVICES=false

for arg in "$@"; do
    case $arg in
        --no-cache)
            NO_CACHE=true
            ;;
        --api|--backend)
            if [ "$EXPLICIT_SERVICES" = false ]; then
                TEST_API=true
                TEST_UI=false
                EXPLICIT_SERVICES=true
            else
                TEST_API=true
            fi
            ;;
        --ui|--frontend)
            if [ "$EXPLICIT_SERVICES" = false ]; then
                TEST_API=false
                TEST_UI=true
                EXPLICIT_SERVICES=true
            else
                TEST_UI=true
            fi
            ;;
        --help)
            echo "Test script for local Docker host (192.168.1.26)"
            echo ""
            echo "Usage: $0 [--api] [--ui] [--no-cache]"
            echo ""
            echo "Options:"
            echo "  --api        Test only API/backend (can combine with --ui)"
            echo "  --backend    Alias for --api"
            echo "  --ui         Test only UI/frontend (can combine with --api)"
            echo "  --frontend   Alias for --ui"
            echo "  --no-cache   Force rebuild without Docker cache"
            echo "  --help       Show this help"
            echo ""
            echo "Examples:"
            echo "  $0               # Test both API and UI (default)"
            echo "  $0 --api        # Test only API"
            echo "  $0 --ui         # Test only UI"
            echo "  $0 --api --ui   # Test both (same as default)"
            echo "  $0 --backend --no-cache  # Test only API with no cache"
            echo ""
            echo "This script builds and tests the application on the remote Docker host"
            echo "to verify everything works before deploying to production."
            echo ""
            exit 0
            ;;
    esac
done

# Configuration
DOCKER_HOST="ssh://adrna@192.168.1.26"
GIT_COMMIT_SHA=$(git rev-parse --short HEAD)
TEST_API_PORT=8101
TEST_UI_PORT=3101

echo "Testing on local Docker host..."
echo "Commit SHA: $GIT_COMMIT_SHA"

if [ "$TEST_API" = true ]; then
    echo "API will be available at: http://192.168.1.26:$TEST_API_PORT"
fi

if [ "$TEST_UI" = true ]; then
    echo "UI will be available at: http://192.168.1.26:$TEST_UI_PORT"
fi

echo "Testing: API=$TEST_API, UI=$TEST_UI"
echo ""

# Export Docker host
export DOCKER_HOST

# Build containers
if [ "$NO_CACHE" = true ]; then
    echo "Building containers (no cache)..."
    docker compose -f docker/docker-compose.yml build --no-cache
else
    echo "Building containers..."
    docker compose -f docker/docker-compose.yml build
fi

# Start containers with test ports
echo "Starting test containers..."
DOCKER_HOST_IP=192.168.1.26 \
GIT_COMMIT_SHA=$GIT_COMMIT_SHA \
DEBUG=true \
API_PORT=$TEST_API_PORT \
UI_PORT=$TEST_UI_PORT \
docker compose -f docker/docker-compose.yml up -d

# Wait for containers to be ready
echo "Waiting for containers to start..."
sleep 10

# Test API health
if [ "$TEST_API" = true ]; then
    echo "Testing API health..."
    if curl -f -s "http://192.168.1.26:$TEST_API_PORT/health" >/dev/null; then
        echo "✅ API is healthy"
        
        # Get API health details
        API_HEALTH=$(curl -s "http://192.168.1.26:$TEST_API_PORT/health")
        echo "   $API_HEALTH"
    else
        echo "❌ API health check failed"
        echo "API logs:"
        docker compose -f docker/docker-compose.yml logs api --tail=20
        exit 1
    fi
fi

# Test UI build info
if [ "$TEST_UI" = true ]; then
    echo "Testing UI build info..."
    if curl -f -s "http://192.168.1.26:$TEST_UI_PORT/build-info.json" >/dev/null; then
        echo "✅ UI is responding"
        
        # Get build info details
        BUILD_INFO=$(curl -s "http://192.168.1.26:$TEST_UI_PORT/build-info.json")
        echo "   $BUILD_INFO"
        
        # Check if git commit SHA is correct
        if echo "$BUILD_INFO" | grep -q "\"commitSha\": \"$GIT_COMMIT_SHA\""; then
            echo "✅ Git commit SHA is correct in build info"
        else
            echo "❌ Git commit SHA mismatch in build info"
            echo "Expected: $GIT_COMMIT_SHA"
            echo "Got: $BUILD_INFO"
            exit 1
        fi
    else
        echo "❌ UI build info check failed"
        echo "UI logs:"
        docker compose -f docker/docker-compose.yml logs ui --tail=20
        exit 1
    fi
fi

# Clean up test containers
echo ""
echo "Cleaning up test containers..."
docker compose -f docker/docker-compose.yml down

echo ""
echo "🎉 All tests passed!"
echo "Ready to deploy to production with commit: $GIT_COMMIT_SHA"