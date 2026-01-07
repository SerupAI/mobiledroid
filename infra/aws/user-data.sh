#!/bin/bash
set -e

# Log everything
exec > >(tee /var/log/user-data.log) 2>&1
echo "Starting setup at $(date)"

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
apt-get install -y ca-certificates curl gnupg
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

# Install kernel modules for redroid (binder, ashmem)
apt-get install -y linux-modules-extra-$(uname -r)

# Load binder module
modprobe binder_linux devices="binder,hwbinder,vndbinder"
modprobe ashmem_linux || true  # ashmem might not be available, binder is essential

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

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Install git
apt-get install -y git

# Create deploy script
cat > /opt/mobiledroid/deploy.sh << 'DEPLOY'
#!/bin/bash
set -e

cd /opt/mobiledroid

# Clone or pull repo
if [ -d "ditto-mobile" ]; then
  cd ditto-mobile
  git pull
else
  git clone https://github.com/serup.ai/ditto-mobile.git
  cd ditto-mobile
fi

# Build and start
cd docker
docker compose down || true
docker compose build
docker compose up -d

echo "Deployment complete!"
docker compose ps
DEPLOY

chmod +x /opt/mobiledroid/deploy.sh
chown ubuntu:ubuntu /opt/mobiledroid/deploy.sh

# Create a simple status check
cat > /opt/mobiledroid/status.sh << 'STATUS'
#!/bin/bash
echo "=== Docker Containers ==="
docker ps -a
echo ""
echo "=== Disk Usage ==="
df -h /
echo ""
echo "=== Memory ==="
free -h
echo ""
echo "=== Kernel Modules ==="
lsmod | grep -E "binder|ashmem" || echo "Modules not loaded"
STATUS

chmod +x /opt/mobiledroid/status.sh
chown ubuntu:ubuntu /opt/mobiledroid/status.sh

echo "Setup complete at $(date)"
echo "Run 'sudo tailscale up' to connect to Tailscale"
echo "Run '/opt/mobiledroid/deploy.sh' to deploy the app"
