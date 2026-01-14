# MobileDroid on Vast.ai

Deploy MobileDroid with GPU acceleration on Vast.ai - the cheapest GPU cloud marketplace.

## Why Vast.ai?

- **Cheapest GPUs**: P2P marketplace with prices 3-5x lower than AWS
- **RTX 4090 from $0.34/hr**: High-end consumer GPUs at fraction of cloud cost
- **Flexible billing**: Per-second, interruptible options for even lower prices
- **Global availability**: GPUs from providers worldwide

## Quick Start

### 1. Create a Vast.ai Account

[![Sign up for Vast.ai](https://img.shields.io/badge/Vast.ai-Sign_Up-00D4AA?style=for-the-badge)](https://cloud.vast.ai/?ref_id=386631)

### 2. Rent a GPU Instance

1. Go to [Vast.ai Console](https://cloud.vast.ai/?ref_id=386631)
2. Click **Search** to find available GPUs
3. Filter by:
   - **GPU Type**: RTX 3090, RTX 4090, or A100
   - **Disk Space**: 50GB minimum
   - **Docker**: Enabled
4. Recommended filters:
   - `gpu_name == "RTX 4090"` for best performance
   - `gpu_name == "RTX 3090"` for best value
5. Click **Rent** on your chosen instance

### 3. Configure Your Instance

When creating the instance:
- **Docker Image**: `nvidia/cuda:12.0-base-ubuntu22.04` or similar
- **Disk Space**: 50GB+
- **Ports**: Add `3100` and `8100` to exposed ports

### 4. Install MobileDroid

SSH into your instance and run:

```bash
curl -fsSL https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/vastai/install.sh | bash
```

### 5. Set Your API Key

```bash
echo "ANTHROPIC_API_KEY=sk-ant-xxx" >> /root/mobiledroid/.env
cd /root/mobiledroid/docker && docker compose restart
```

## Accessing MobileDroid

After installation, access via the public IP shown in your Vast.ai dashboard:

- **Web UI**: `http://[instance-ip]:3100`
- **API**: `http://[instance-ip]:8100`

Make sure ports 3100 and 8100 are exposed in your instance configuration.

## Cost Comparison

| Provider | GPU | Hourly | Monthly (24/7) |
|----------|-----|--------|----------------|
| **Vast.ai** | RTX 3090 | ~$0.20 | ~$146 |
| **Vast.ai** | RTX 4090 | ~$0.34 | ~$248 |
| RunPod | RTX 3090 | $0.22 | ~$160 |
| AWS | T4 (g4dn) | $0.53 | ~$386 |
| AWS | A10G (g5) | $0.92 | ~$672 |

**Vast.ai can be 2-4x cheaper than other providers.**

## Instance Selection Tips

### Best Value
- **RTX 3090** at $0.15-0.25/hr
- 24GB VRAM, excellent for MobileDroid
- Look for "unverified" hosts for lowest prices

### Best Performance
- **RTX 4090** at $0.30-0.40/hr
- Fastest consumer GPU
- Great for heavy automation workloads

### Enterprise
- **A100 40GB/80GB** at $1.00-2.00/hr
- Professional-grade reliability
- Best for multi-profile setups

## GPU Verification

Check that your GPU is working:

```bash
nvidia-smi
```

Expected output shows your GPU with memory and utilization.

## Troubleshooting

### Instance won't start

1. Check your Vast.ai balance (minimum $5)
2. Try a different provider/instance
3. Some hosts may be temporarily unavailable

### Docker issues

```bash
# Restart Docker
service docker restart

# Check Docker status
docker info
```

### Ports not accessible

1. Verify ports 3100 and 8100 are in "Direct Port Mappings"
2. Check instance firewall settings
3. Some providers block certain ports

### Instance interrupted

Vast.ai marketplace instances can be interrupted by the host:
- Enable "On-Demand" for guaranteed uptime (costs more)
- Or use auto-restart scripts to resume work

## Saving Costs

### Use Interruptible Instances
- Up to 50% cheaper
- May be stopped by host
- Good for non-critical workloads

### Stop When Not in Use
1. Go to Vast.ai dashboard
2. Click **Stop** on your instance
3. You keep paying for storage only
4. Click **Start** to resume

### Bid Lower
- Set maximum price below market rate
- Instance starts when price drops
- Great for flexible workloads

## Need Help?

- [MobileDroid Discord](https://discord.gg/rP5PAjG3jx)
- [Vast.ai Discord](https://discord.gg/vast-ai)
- [GitHub Issues](https://github.com/serup-ai/mobiledroid/issues)
