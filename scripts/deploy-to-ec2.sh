#!/bin/bash

# Deploy script for EC2
# Usage: ./deploy-to-ec2.sh [tag]
#   tag: Optional git tag to deploy (e.g., v0.0.1)
#        If not provided, deploys current local code

TAG=$1

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
echo "Building and restarting containers..."
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "cd /home/ubuntu/mobiledroid && set -a && source .env && set +a && DOCKER_HOST_IP=$EC2_HOST GIT_COMMIT_SHA=$GIT_COMMIT_SHA docker compose -f docker/docker-compose.yml up -d --build"

echo "Deployment complete!"
if [ "$DEPLOY_MODE" = "tag" ]; then
    echo "Deployed tag: $TAG (commit: $GIT_COMMIT_SHA)"
else
    echo "Deployed local code (commit: $GIT_COMMIT_SHA)"
fi
echo ""
echo "UI: http://$EC2_HOST:3100"
echo "API: http://$EC2_HOST:8100"  
echo "API Docs: http://$EC2_HOST:8100/docs"