# MobileDroid on RunPod

Deploy MobileDroid with GPU acceleration on RunPod for the best price/performance.

## Why RunPod?

- **Cheap GPUs**: RTX 3090 from $0.22/hr (vs AWS g4dn at $0.53/hr)
- **Per-second billing**: Only pay for what you use
- **Pre-configured templates**: Docker and NVIDIA drivers ready
- **Community Cloud**: Even cheaper spot-like pricing

## Quick Start

### 1. Create a RunPod Account

[![Sign up for RunPod](https://img.shields.io/badge/RunPod-Sign_Up-673AB7?style=for-the-badge&logo=runpod)](https://runpod.io?ref=h9kmgkc7)

### 2. Create a Pod

1. Go to [Pods](https://www.runpod.io/console/pods)
2. Click **Deploy**
3. Select a GPU:
   - **Budget**: RTX 3090 (24GB) - $0.22-0.43/hr
   - **Performance**: RTX 4090 (24GB) - $0.34-0.69/hr
   - **Enterprise**: A100 (80GB) - $1.19-1.64/hr
4. Choose template: **RunPod Pytorch** or **Ubuntu 22.04**
5. Set container disk: **50GB minimum**
6. Expose ports: **3100** (UI), **8100** (API)
7. Deploy!

### 3. Install MobileDroid

SSH into your pod and run:

```bash
curl -fsSL https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/runpod/install.sh | bash
```

### 4. Set Your API Key

```bash
echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> /workspace/mobiledroid/.env
cd /workspace/mobiledroid/docker && docker compose restart
```

## Accessing MobileDroid

RunPod provides public URLs for exposed ports:

- **Web UI**: `https://[pod-id]-3100.proxy.runpod.net`
- **API**: `https://[pod-id]-8100.proxy.runpod.net`

Or use the direct IP shown in your pod details.

## Cost Comparison

| Provider | GPU | Hourly | Monthly (24/7) |
|----------|-----|--------|----------------|
| **RunPod** | RTX 3090 | $0.22 | ~$160 |
| **RunPod** | RTX 4090 | $0.34 | ~$248 |
| AWS | T4 (g4dn) | $0.53 | ~$386 |
| AWS | A10G (g5) | $0.92 | ~$672 |

**RunPod is 2-3x cheaper than AWS for GPU workloads.**

## GPU Verification

Check that your GPU is working:

```bash
nvidia-smi
```

You should see your GPU listed with memory and utilization stats.

## Troubleshooting

### Docker not starting containers

```bash
# Check Docker status
systemctl status docker

# Restart Docker
systemctl restart docker
```

### GPU not detected in containers

```bash
# Verify NVIDIA runtime is configured
docker info | grep -i nvidia

# Test GPU access
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### Services not accessible

1. Verify ports 3100 and 8100 are exposed in pod settings
2. Check pod status in RunPod dashboard
3. View logs: `docker compose logs -f`

## Stopping Your Pod

To save costs when not using MobileDroid:

1. Go to RunPod dashboard
2. Click **Stop** on your pod
3. Your data persists on the volume
4. Click **Start** to resume

## Need Help?

- [MobileDroid Discord](https://discord.gg/rP5PAjG3jx)
- [RunPod Discord](https://discord.gg/runpod)
- [GitHub Issues](https://github.com/serup-ai/mobiledroid/issues)
