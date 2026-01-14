# macOS Setup

MobileDroid can run on macOS using Docker Desktop, but with limitations.

## Limitations on macOS

- **No native KVM**: macOS uses a HyperKit/Apple Hypervisor VM for Docker
- **No kernel modules**: binder_linux and ashmem_linux aren't available
- **Performance**: Slower than native Linux due to VM overhead
- **Redroid issues**: May not work reliably without kernel modules

**Recommendation**: For the best experience, use [cloud deployment](../deploy/README.md) (AWS, RunPod, or Vast.ai).

## Option 1: Cloud Deployment (Recommended)

Deploy MobileDroid to a cloud provider and access via your browser:

| Provider | Cost | Setup |
|----------|------|-------|
| [DigitalOcean](../deploy/digitalocean/README.md) | $24-48/mo | One-click droplet |
| [RunPod](../deploy/runpod/README.md) | $0.22/hr | GPU cloud |
| [Vast.ai](../deploy/vastai/README.md) | $0.20/hr | Cheapest GPU |
| [AWS](../deploy/aws/README.md) | $50-150/mo | CloudFormation |

## Option 2: Local Docker (Experimental)

If you want to try running locally:

### Requirements

- **macOS**: 12.0 (Monterey) or later
- **RAM**: 16GB minimum
- **Docker Desktop**: 4.0+
- **Disk**: 50GB+ free space

### Install Docker Desktop

1. Download from [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. Install and start Docker Desktop
3. Allocate resources in Settings:
   - Memory: 8GB minimum
   - Disk: 50GB+
   - CPUs: 4+

### Clone and Run

```bash
# Clone repository
git clone https://github.com/serup-ai/mobiledroid.git
cd mobiledroid

# Create environment file
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# Start services (may have issues with Redroid)
cd docker
docker compose up -d
```

### Expected Issues

The Android container (Redroid) likely won't start because macOS Docker doesn't have:
- `/dev/binder` device
- `ashmem` shared memory
- KVM acceleration

You'll see errors like:
```
binder_linux module not loaded
```

### Workaround: API-Only Mode

You can run just the API and UI for development, without the Android container:

```bash
# Start only API and database
docker compose up -d db redis api ui

# Android features won't work, but you can develop the API
```

## Option 3: Linux VM on macOS

Run a full Linux VM using:

### UTM (Apple Silicon)

1. Download [UTM](https://mac.getutm.app/)
2. Create Ubuntu 22.04 VM
3. Allocate 8GB+ RAM, 4+ CPUs
4. Follow [Linux setup instructions](./linux.md) inside VM

### Parallels Desktop

1. Install Parallels Desktop
2. Create Ubuntu 22.04 VM with nested virtualization enabled
3. Follow [Linux setup instructions](./linux.md)

### VMware Fusion

1. Install VMware Fusion
2. Create Ubuntu 22.04 VM
3. Enable nested virtualization in VM settings
4. Follow [Linux setup instructions](./linux.md)

## Development on macOS

For developing MobileDroid code (not running Android):

### API Development

```bash
cd packages/api

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run API (needs database)
docker compose up -d db redis
uvicorn src.main:app --reload --port 8100
```

### UI Development

```bash
cd packages/ui

# Install dependencies
npm install

# Run dev server
npm run dev
```

Access at http://localhost:3000

## SSH to Cloud Instance

If using cloud deployment, connect from your Mac:

```bash
# DigitalOcean/Vultr
ssh root@your-server-ip

# AWS
ssh -i your-key.pem ubuntu@your-server-ip
```

Then access MobileDroid at `http://your-server-ip:3100`

## Need Help?

- [Discord Community](https://discord.gg/rP5PAjG3jx)
- [GitHub Issues](https://github.com/serup-ai/mobiledroid/issues)
