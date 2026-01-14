# Linux Setup (Recommended)

MobileDroid runs best on Linux with native kernel module support.

## Requirements

- **OS**: Ubuntu 22.04+, Debian 12+, or similar
- **Kernel**: 5.4+ (for binder/ashmem modules)
- **RAM**: 8GB minimum (16GB recommended)
- **Docker**: Docker Engine 24.0+ with Compose
- **Disk**: 50GB+ free space

## Quick Start

### 1. Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Add your user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker
```

### 2. Load Kernel Modules

MobileDroid uses Redroid (Android in Docker) which requires special kernel modules:

```bash
# Load modules
sudo modprobe binder_linux devices="binder,hwbinder,vndbinder"
sudo modprobe ashmem_linux

# Verify they loaded
lsmod | grep -E "binder|ashmem"
```

### 3. Persist Modules on Boot

```bash
# Add to /etc/modules
echo "binder_linux" | sudo tee -a /etc/modules
echo "ashmem_linux" | sudo tee -a /etc/modules

# For binder options, create config file
echo 'options binder_linux devices="binder,hwbinder,vndbinder"' | sudo tee /etc/modprobe.d/binder.conf
```

### 4. Clone and Run MobileDroid

```bash
# Clone repository
git clone https://github.com/serup-ai/mobiledroid.git
cd mobiledroid

# Create environment file
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# Start services
cd docker
docker compose up -d
```

### 5. Access MobileDroid

- **Web UI**: http://localhost:3100
- **API**: http://localhost:8100
- **API Docs**: http://localhost:8100/docs

## GPU Acceleration (Optional)

If you have an NVIDIA GPU, enable hardware acceleration:

### Install NVIDIA Drivers

```bash
# Ubuntu/Debian
sudo apt install nvidia-driver-535

# Reboot
sudo reboot
```

### Install NVIDIA Container Toolkit

```bash
# Add NVIDIA repo
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
  sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Install toolkit
sudo apt update
sudo apt install nvidia-container-toolkit

# Configure Docker
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Enable GPU in MobileDroid

Edit your `.env` file:

```bash
REDROID_GPU_MODE=host
```

Restart services:

```bash
cd docker && docker compose restart
```

## Troubleshooting

### Kernel modules not loading

**Error**: `modprobe: FATAL: Module binder_linux not found`

Your kernel may not have these modules. Solutions:

1. **Check kernel version**: `uname -r` (needs 5.4+)
2. **Install kernel headers**: `sudo apt install linux-headers-$(uname -r)`
3. **Use a cloud provider** with pre-configured kernels (AWS, DigitalOcean)

### Docker permission denied

**Error**: `permission denied while trying to connect to the Docker daemon`

```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Apply without logout
newgrp docker
```

### Container won't start

Check logs:

```bash
docker compose logs api
docker compose logs redroid
```

Common issues:
- Not enough disk space
- Port already in use (change in `.env`)
- Missing kernel modules

### Android container fails

```bash
# Check if binder is available
ls -la /dev/binder*

# Check container logs
docker logs mobiledroid-redroid-1
```

## Firewall Configuration

If using `ufw`:

```bash
sudo ufw allow 3100/tcp  # Web UI
sudo ufw allow 8100/tcp  # API
```

If using `firewalld`:

```bash
sudo firewall-cmd --add-port=3100/tcp --permanent
sudo firewall-cmd --add-port=8100/tcp --permanent
sudo firewall-cmd --reload
```

## Distribution-Specific Notes

### Ubuntu 22.04/24.04
- Kernel modules available by default
- Best supported distribution

### Debian 12
- May need to install `linux-headers` package
- Works well after module setup

### Fedora/RHEL
- Use `dnf` instead of `apt`
- SELinux may require additional configuration

### Arch Linux
- Modules available in `linux` package
- May need to build from AUR for older kernels

## Need Help?

- [Discord Community](https://discord.gg/rP5PAjG3jx)
- [GitHub Issues](https://github.com/serup-ai/mobiledroid/issues)
