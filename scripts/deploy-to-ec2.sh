#!/bin/bash

# Deploy script for EC2

# Get git commit SHA
GIT_COMMIT_SHA=$(git rev-parse --short HEAD)
echo "Deploying commit: $GIT_COMMIT_SHA"

# Export for docker-compose
export GIT_COMMIT_SHA

# EC2 details
EC2_HOST="34.235.77.142"
EC2_USER="ubuntu"
SSH_KEY="infra/aws/mobiledroid-key.pem"

# Sync code to EC2
echo "Syncing code to EC2..."
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

# Build and restart containers on EC2
echo "Building and restarting containers..."
ssh -i $SSH_KEY $EC2_USER@$EC2_HOST "cd /home/ubuntu/mobiledroid && set -a && source .env && set +a && DOCKER_HOST_IP=$EC2_HOST GIT_COMMIT_SHA=$GIT_COMMIT_SHA docker compose -f docker/docker-compose.yml up -d --build"

echo "Deployment complete!"
echo "UI: http://$EC2_HOST:3100"
echo "API: http://$EC2_HOST:8100"
echo "API Docs: http://$EC2_HOST:8100/docs"