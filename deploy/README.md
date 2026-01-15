# Deploy MobileDroid

One-click deployment options for running your own MobileDroid instance.

## Requirements

MobileDroid requires:
- **Linux** with kernel 5.4+ (for Android container support)
- **2+ vCPU, 4GB+ RAM** minimum (4 vCPU, 8GB recommended)
- **Docker** and Docker Compose
- **Privileged containers** (for Redroid Android emulation)
- **Kernel modules**: binder_linux, ashmem_linux
- **Ports**: 3100 (UI), 8100 (API), 22 (SSH)

> **Note**: Container platforms (Railway, Render, Heroku, DigitalOcean App Platform) do not support the privileged containers required for Android emulation. Use VM-based deployments below instead.

---

## AWS (CloudFormation)

Launch MobileDroid on AWS EC2 with one click:

| Region | Launch |
|--------|--------|
| US East (N. Virginia) | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |
| US East (Ohio) | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-2#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |
| US West (N. California) | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-1#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |
| US West (Oregon) | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-west-2#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |
| EU (Ireland) | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |
| EU (Frankfurt) | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=eu-central-1#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |
| Asia Pacific (Singapore) | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=ap-southeast-1#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |
| Asia Pacific (Tokyo) | [![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=ap-northeast-1#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |

**Estimated cost**: ~$50-150/month depending on instance type

### AWS GPU (Better Performance)

For graphics-intensive automation, use GPU-accelerated instances:

| Instance | GPU | Cost | Launch |
|----------|-----|------|--------|
| g4dn.xlarge | NVIDIA T4 | ~$0.53/hr | [![Launch GPU Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=mobiledroid-gpu&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation-gpu.yaml) |
| g6.xlarge | NVIDIA L4 | ~$0.80/hr | [![Launch GPU Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=mobiledroid-gpu&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation-gpu.yaml) |

---

## DigitalOcean

### Option 1: Create Droplet + Run Script

1. Create an Ubuntu 22.04 Droplet (minimum: s-2vcpu-4gb)

   [![Create Droplet](https://img.shields.io/badge/DigitalOcean-Create_Droplet-0080FF?style=for-the-badge&logo=digitalocean)](https://m.do.co/c/c14767268755)

2. SSH into your droplet and run:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/digitalocean/install.sh | sudo bash
   ```

3. Set your API key:
   ```bash
   echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> /opt/mobiledroid/.env
   cd /opt/mobiledroid/docker && docker compose restart
   ```

**Estimated cost**: ~$24-48/month

---

## Vultr

### Option 1: Create Instance + Run Script

1. Create an Ubuntu 22.04 Cloud Compute instance (minimum: 2 vCPU, 4GB RAM)

   [![Deploy on Vultr](https://img.shields.io/badge/Vultr-Deploy_Instance-007BFC?style=for-the-badge&logo=vultr)](https://www.vultr.com/?ref=9853720)

2. SSH into your instance and run:
   ```bash
   curl -fsSL https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/vultr/install.sh | sudo bash
   ```

3. Set your API key:
   ```bash
   echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> /opt/mobiledroid/.env
   cd /opt/mobiledroid/docker && docker compose restart
   ```

**Estimated cost**: ~$24-48/month

---

## GPU Cloud (Best Value)

For the best price-to-performance GPU hosting, use specialized GPU clouds:

### RunPod

[![Deploy on RunPod](https://img.shields.io/badge/RunPod-Deploy_GPU-673AB7?style=for-the-badge&logo=runpod)](https://runpod.io?ref=h9kmgkc7)

- **RTX 3090**: $0.22-0.43/hr (vs AWS $0.53/hr)
- **RTX 4090**: $0.34-0.69/hr
- Per-second billing, no hourly minimums

[Full RunPod Setup Guide](runpod/README.md)

### Vast.ai

[![Deploy on Vast.ai](https://img.shields.io/badge/Vast.ai-Deploy_GPU-00D4AA?style=for-the-badge)](https://cloud.vast.ai/?ref_id=386631)

- **RTX 3090**: ~$0.20/hr (cheapest option)
- **RTX 4090**: ~$0.34/hr
- P2P marketplace with lowest prices

[Full Vast.ai Setup Guide](vastai/README.md)

### GPU Cost Comparison

| Provider | GPU | Hourly | Monthly (24/7) |
|----------|-----|--------|----------------|
| Vast.ai | RTX 3090 | ~$0.20 | ~$146 |
| RunPod | RTX 3090 | ~$0.22 | ~$160 |
| AWS | T4 (g4dn) | $0.53 | ~$386 |
| AWS | L4 (g6) | $0.80 | ~$584 |

---

## Manual Installation (Any VPS)

Works on any Linux VPS with Docker support:

```bash
# Clone the repository
git clone https://github.com/serup-ai/mobiledroid.git
cd mobiledroid

# Create .env file
cp .env.example .env
nano .env  # Add your ANTHROPIC_API_KEY

# Load kernel modules (for Android containers)
sudo modprobe binder_linux devices="binder,hwbinder,vndbinder"
sudo modprobe ashmem_linux

# Start services
cd docker
docker compose up -d
```

Access:
- UI: http://YOUR_IP:3100
- API: http://YOUR_IP:8100

---

## Post-Installation

### Set Anthropic API Key

The AI agent requires an Anthropic API key. Get one at: https://console.anthropic.com/

```bash
# Edit the .env file
nano /opt/mobiledroid/.env

# Add your key
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Restart services
cd /opt/mobiledroid/docker
docker compose restart
```

### Configure Firewall

Make sure these ports are open:
- **3100** - Web UI
- **8100** - API server
- **22** - SSH (restrict to your IP)

### View Logs

```bash
cd /opt/mobiledroid/docker
docker compose logs -f
```

---

## Troubleshooting

### Android containers not starting

The kernel may not have binder/ashmem modules. Check:
```bash
lsmod | grep binder
lsmod | grep ashmem
```

If missing, you may need a kernel with these modules or use a provider that supports nested virtualization.

### Services not starting

Check logs:
```bash
cd /opt/mobiledroid/docker
docker compose logs api
docker compose logs ui
```

---

## Local Development Setup

Running MobileDroid locally? See platform-specific guides:

| Platform | Guide | Notes |
|----------|-------|-------|
| **Linux** | [Setup Guide](../docs/setup/linux.md) | Recommended - native support |
| **Windows (WSL2)** | [Setup Guide](../docs/setup/windows-wsl.md) | Requires custom kernel |
| **macOS** | [Setup Guide](../docs/setup/macos.md) | Limited - use cloud instead |

---

## Need Help?

### Community Support (Free)

- [Discord Community](https://discord.gg/rP5PAjG3jx) - Get help, share feedback
- [GitHub Issues](https://github.com/serup-ai/mobiledroid/issues) - Report bugs
- [GitHub Discussions](https://github.com/serup-ai/mobiledroid/discussions) - Ask questions

### Professional Services

Need help with deployment, customization, or enterprise integration?

**Consulting available** for:
- Custom deployment and architecture
- AWS/cloud infrastructure setup
- Enterprise integration and scaling
- Training and onboarding

[Contact us on Discord](https://discord.gg/rP5PAjG3jx) or reach out directly to discuss your requirements.
