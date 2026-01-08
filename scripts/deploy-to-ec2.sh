#!/bin/bash

# Deploy script for EC2
# Usage: ./deploy-to-ec2.sh [tag] [options]
#   tag: Optional git tag to deploy (e.g., v0.0.1)
#        If not provided, deploys current local code
#
# Options:
#   --build      Force rebuild containers (default)
#   --no-build   Skip building, just restart existing containers  
#   --no-cache   Force rebuild without Docker cache
#   --help       Show this help

# Parse arguments
TAG=""
BUILD_MODE="build"      # build, no-build, no-cache
HELP=false

for arg in "$@"; do
    case $arg in
        --build)
            BUILD_MODE="build"
            ;;
        --no-build)
            BUILD_MODE="no-build"
            ;;
        --no-cache)
            BUILD_MODE="no-cache"
            ;;
        --help)
            HELP=true
            ;;
        --*)
            echo "Unknown option: $arg"
            exit 1
            ;;
        *)
            if [[ -z "$TAG" ]]; then
                TAG="$arg"
            else
                echo "Multiple tags specified: $TAG and $arg"
                exit 1
            fi
            ;;
    esac
done

if [[ "$HELP" == true ]]; then
    echo "Deploy script for EC2"
    echo ""
    echo "Usage: $0 [tag] [options]"
    echo ""
    echo "Arguments:"
    echo "  tag          Git tag to deploy (e.g., v0.0.1). If not provided, deploys current local code"
    echo ""
    echo "Options:"
    echo "  --build      Force rebuild containers (default)"
    echo "  --no-build   Skip building, just restart existing containers"
    echo "  --no-cache   Force rebuild without Docker cache (slow but ensures fresh build)"
    echo "  --help       Show this help"
    echo ""
    echo "Examples:"
    echo "  $0                           # Deploy local code with rebuild"
    echo "  $0 v0.0.1                    # Deploy tag v0.0.1 with rebuild"
    echo "  $0 --no-build               # Restart containers without rebuilding"
    echo "  $0 v0.0.1 --no-cache        # Deploy tag with fresh rebuild (no cache)"
    echo ""
    exit 0
fi

if [ -n "$TAG" ]; then
    echo "Deploying tag: $TAG"
    # For tag deployment, we'll checkout the tag on the remote server
    DEPLOY_MODE="tag"
    GIT_COMMIT_SHA=$(git rev-parse --short $TAG 2>/dev/null || echo "unknown")
else
    # Get current local commit SHA
    GIT_COMMIT_SHA=$(git rev-parse --short HEAD)
    echo "Deploying local commit: $GIT_COMMIT_SHA"
    DEPLOY_MODE="local"
fi

# Export for docker-compose
export GIT_COMMIT_SHA

# EC2 details
EC2_HOST="34.235.77.142"
EC2_USER="ubuntu"
SSH_KEY="infra/aws/mobiledroid-key.pem"

if [ "$DEPLOY_MODE" = "tag" ]; then
    echo "Deploying tag $TAG..."
    
    # Verify tag exists
    if ! git tag -l | grep -q "^$TAG$"; then
        echo "Error: Tag $TAG not found locally. Available tags:"
        git tag -l
        exit 1
    fi
    
    # Create temporary directory for tag contents
    TEMP_DIR=$(mktemp -d)
    echo "Extracting tag $TAG to temporary directory: $TEMP_DIR"
    
    # Extract tag contents to temporary directory
    git archive $TAG | tar -x -C $TEMP_DIR
    
    # Sync tag contents to EC2
    echo "Syncing tag $TAG code to EC2..."
    rsync -avz \
      --exclude 'node_modules' \
      --exclude '.next' \
      --exclude '__pycache__' \
      --exclude 'venv' \
      --exclude '.git' \
      --exclude 'terraform.tfstate*' \
      --exclude '*.pem' \
      --delete \
      -e "ssh -i $SSH_KEY" \
      $TEMP_DIR/ $EC2_USER@$EC2_HOST:/home/ubuntu/mobiledroid/
      
    # Cleanup temporary directory
    rm -rf $TEMP_DIR
    echo "Cleaned up temporary directory"
    
else
    # Sync local code to EC2
    echo "Syncing local code to EC2..."
    rsync -avz \
      --exclude 'node_modules' \
      --exclude '.next' \
      --exclude '__pycache__' \
      --exclude 'venv' \
      --exclude '.git' \
      --exclude 'terraform.tfstate*' \
      --exclude '*.pem' \
      -e "ssh -i $SSH_KEY" \
      ./ $EC2_USER@$EC2_HOST:/home/ubuntu/mobiledroid/
fi

# Build and restart containers on EC2
case $BUILD_MODE in
    "no-build")
        echo "Restarting containers without building..."
        ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "cd /home/ubuntu/mobiledroid && set -a && source .env 2>/dev/null || true && set +a && DOCKER_HOST_IP=$EC2_HOST GIT_COMMIT_SHA=$GIT_COMMIT_SHA DEBUG=true docker compose -f docker/docker-compose.yml up -d"
        ;;
    "no-cache")
        echo "Building and restarting containers (no cache)..."
        ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "cd /home/ubuntu/mobiledroid && set -a && source .env 2>/dev/null || true && set +a && docker compose -f docker/docker-compose.yml down && DOCKER_HOST_IP=$EC2_HOST GIT_COMMIT_SHA=$GIT_COMMIT_SHA DEBUG=true docker compose -f docker/docker-compose.yml build --no-cache && DOCKER_HOST_IP=$EC2_HOST GIT_COMMIT_SHA=$GIT_COMMIT_SHA DEBUG=true docker compose -f docker/docker-compose.yml up -d"
        ;;
    "build"|*)
        echo "Building and restarting containers..."
        ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "cd /home/ubuntu/mobiledroid && set -a && source .env 2>/dev/null || true && set +a && DOCKER_HOST_IP=$EC2_HOST GIT_COMMIT_SHA=$GIT_COMMIT_SHA DEBUG=true docker compose -f docker/docker-compose.yml up -d --build"
        ;;
esac

echo "Deployment complete!"
if [ "$DEPLOY_MODE" = "tag" ]; then
    echo "Deployed tag: $TAG (commit: $GIT_COMMIT_SHA) [build-mode: $BUILD_MODE]"
else
    echo "Deployed local code (commit: $GIT_COMMIT_SHA) [build-mode: $BUILD_MODE]"
fi
echo ""
echo "UI: http://$EC2_HOST:3100"
echo "API: http://$EC2_HOST:8100"  
echo "API Docs: http://$EC2_HOST:8100/docs"