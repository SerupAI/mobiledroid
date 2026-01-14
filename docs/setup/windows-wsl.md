# Windows WSL2 Setup

MobileDroid can run on Windows using WSL2 (Windows Subsystem for Linux), but requires a custom kernel with Android support modules.

## Requirements

- **Windows**: 10 (build 19041+) or Windows 11
- **WSL2**: Enabled with Ubuntu 22.04
- **RAM**: 16GB minimum (WSL2 shares with Windows)
- **Disk**: 50GB+ free space
- **Admin access**: Required for WSL configuration

## Difficulty Level: Advanced

This setup requires building a custom WSL kernel. If you're not comfortable with kernel compilation, consider using [cloud deployment](../deploy/README.md) instead.

## Quick Path: Cloud Deployment

For easiest setup from Windows, deploy to cloud and access via browser:

| Provider | Cost | Setup |
|----------|------|-------|
| [DigitalOcean](../deploy/digitalocean/README.md) | $24-48/mo | One-click |
| [RunPod](../deploy/runpod/README.md) | $0.22/hr | GPU cloud |
| [AWS](../deploy/aws/README.md) | $50-150/mo | CloudFormation |

## Full WSL2 Setup

### Step 1: Enable WSL2

Open PowerShell as Administrator:

```powershell
# Enable WSL
wsl --install

# Set WSL2 as default
wsl --set-default-version 2

# Install Ubuntu 22.04
wsl --install -d Ubuntu-22.04
```

Restart your computer.

### Step 2: Install Build Dependencies

In your WSL2 Ubuntu terminal:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install build tools
sudo apt install -y build-essential flex bison libssl-dev libelf-dev \
    bc dwarves libncurses-dev git
```

### Step 3: Build Custom WSL Kernel

The default WSL kernel doesn't include Android binder/ashmem modules. We need to build a custom one.

```bash
# Clone Microsoft's WSL2 kernel
git clone --depth 1 https://github.com/microsoft/WSL2-Linux-Kernel.git
cd WSL2-Linux-Kernel

# Copy current config
cp Microsoft/config-wsl .config

# Enable Android modules
cat >> .config << 'EOF'
CONFIG_ANDROID=y
CONFIG_ANDROID_BINDER_IPC=y
CONFIG_ANDROID_BINDERFS=y
CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"
CONFIG_ASHMEM=y
EOF

# Build kernel (takes 15-30 minutes)
make -j$(nproc)

# Copy kernel to Windows
cp arch/x86/boot/bzImage /mnt/c/Users/$USER/wsl-kernel-android
```

### Step 4: Configure WSL to Use Custom Kernel

Create or edit `.wslconfig` in your Windows user folder:

**File**: `C:\Users\YourUsername\.wslconfig`

```ini
[wsl2]
kernel=C:\\Users\\YourUsername\\wsl-kernel-android
memory=8GB
processors=4
```

### Step 5: Restart WSL

In PowerShell:

```powershell
wsl --shutdown
wsl
```

### Step 6: Verify Kernel Modules

Back in WSL2 Ubuntu:

```bash
# Check kernel version (should show your custom build)
uname -r

# Load modules
sudo modprobe binder_linux devices="binder,hwbinder,vndbinder"
sudo modprobe ashmem_linux

# Verify they loaded
lsmod | grep -E "binder|ashmem"
```

### Step 7: Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com | sudo sh

# Start Docker service
sudo service docker start

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Step 8: Run MobileDroid

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

### Step 9: Access MobileDroid

From Windows browser:
- **Web UI**: http://localhost:3100
- **API**: http://localhost:8100

## Troubleshooting

### Modules not loading

**Error**: `modprobe: FATAL: Module binder_linux not found`

Your custom kernel wasn't applied:
1. Check `.wslconfig` path is correct
2. Run `wsl --shutdown` and restart
3. Verify with `uname -r` (should show your build)

### Docker won't start

```bash
# Start Docker service manually
sudo service docker start

# Or restart WSL
wsl --shutdown  # in PowerShell
wsl             # restart
```

### WSL2 networking issues

Windows Firewall may block WSL2:

1. Open Windows Security
2. Firewall & network protection
3. Allow an app through firewall
4. Add `vmmemproxy` and Docker-related processes

### Memory issues

Edit `.wslconfig` to allocate more RAM:

```ini
[wsl2]
memory=12GB
```

### Kernel build fails

Common fixes:
- Install missing dependencies: `sudo apt install libelf-dev bc flex bison`
- Use exact kernel version: `git checkout linux-msft-wsl-5.15.y`

## Alternative: Docker Desktop for Windows

Docker Desktop includes its own Linux VM, but has same limitations as macOS:
- No kernel modules
- Redroid won't work

Only useful for API/UI development, not running Android containers.

## GPU Passthrough (Experimental)

WSL2 supports GPU passthrough with Windows 11:

1. Install [NVIDIA CUDA drivers for WSL](https://developer.nvidia.com/cuda/wsl)
2. Test with: `nvidia-smi` in WSL
3. May help with some performance, but kernel modules still required

## Persisting Modules

Make modules load on WSL start:

```bash
# Create startup script
sudo nano /etc/wsl.conf
```

Add:
```ini
[boot]
command="modprobe binder_linux devices='binder,hwbinder,vndbinder' && modprobe ashmem_linux"
```

## Need Help?

- [Discord Community](https://discord.gg/rP5PAjG3jx)
- [GitHub Issues](https://github.com/serup-ai/mobiledroid/issues)
- [WSL GitHub Issues](https://github.com/microsoft/WSL/issues)
