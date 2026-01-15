#!/bin/bash
set -e

# Log everything
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting MobileDroid setup at $(date)"

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y ca-certificates curl gnupg git
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add ubuntu user to docker group
usermod -aG docker ubuntu

# Install kernel modules for Redroid (Android containers)
apt-get install -y linux-modules-extra-$(uname -r)

# Load binder module (required for Android emulation)
modprobe binder_linux devices="binder,hwbinder,vndbinder"
modprobe ashmem_linux || true  # ashmem might not be available

# Make modules load on boot
cat >> /etc/modules-load.d/redroid.conf << 'EOF'
binder_linux
ashmem_linux
EOF

cat >> /etc/modprobe.d/redroid.conf << 'EOF'
options binder_linux devices="binder,hwbinder,vndbinder"
EOF

# Create app directory
mkdir -p /opt/mobiledroid
chown ubuntu:ubuntu /opt/mobiledroid

# Clone MobileDroid
cd /opt/mobiledroid
git clone https://github.com/serup-ai/mobiledroid.git app
chown -R ubuntu:ubuntu app

# Create .env file with API keys if provided
cat > /opt/mobiledroid/app/.env << 'ENVFILE'
# MobileDroid Environment Configuration
# Add your API keys here

# Required for AI agent
ANTHROPIC_API_KEY=${anthropic_api_key}

# Optional
OPENAI_API_KEY=${openai_api_key}

# Debug mode (shows build info in UI)
DEBUG=false
NEXT_PUBLIC_DEBUG=false
ENVFILE

chown ubuntu:ubuntu /opt/mobiledroid/app/.env
chmod 600 /opt/mobiledroid/app/.env

# Start MobileDroid
cd /opt/mobiledroid/app/docker
docker compose up -d --build

# Create helper scripts
cat > /opt/mobiledroid/status.sh << 'STATUS'
#!/bin/bash
echo "=== MobileDroid Status ==="
echo ""
echo "=== Docker Containers ==="
cd /opt/mobiledroid/app/docker && docker compose ps
echo ""
echo "=== Kernel Modules ==="
lsmod | grep -E "binder|ashmem" || echo "WARNING: Required modules not loaded"
echo ""
echo "=== Disk Usage ==="
df -h /
echo ""
echo "=== Memory ==="
free -h
STATUS

cat > /opt/mobiledroid/logs.sh << 'LOGS'
#!/bin/bash
cd /opt/mobiledroid/app/docker && docker compose logs -f --tail 100
LOGS

cat > /opt/mobiledroid/restart.sh << 'RESTART'
#!/bin/bash
cd /opt/mobiledroid/app/docker && docker compose restart
RESTART

cat > /opt/mobiledroid/update.sh << 'UPDATE'
#!/bin/bash
set -e
cd /opt/mobiledroid/app
git pull
cd docker
docker compose down
docker compose up -d --build
echo "Update complete!"
docker compose ps
UPDATE

chmod +x /opt/mobiledroid/*.sh
chown ubuntu:ubuntu /opt/mobiledroid/*.sh

echo ""
echo "=========================================="
echo "MobileDroid setup complete at $(date)"
echo "=========================================="
echo ""
echo "Access:"
echo "  UI:  http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):3100"
echo "  API: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8100"
echo ""
echo "Helper scripts in /opt/mobiledroid/:"
echo "  ./status.sh  - Check system status"
echo "  ./logs.sh    - View container logs"
echo "  ./restart.sh - Restart services"
echo "  ./update.sh  - Pull latest and restart"
echo ""
