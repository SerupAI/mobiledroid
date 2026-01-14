# MobileDroid

Self-hosted AI-powered Android device automation platform. Control Android emulators via natural language with multi-profile antidetect support.

[![Discord](https://img.shields.io/badge/Discord-Join_Server-7289da?logo=discord&logoColor=white)](https://discord.gg/rP5PAjG3jx)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## One-Click Deploy

Deploy MobileDroid to your own cloud infrastructure:

| Platform | Deploy |
|----------|--------|
| **AWS** | [![Launch Stack](https://img.shields.io/badge/AWS-Launch_Stack-FF9900?logo=amazon-aws)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/new?stackName=mobiledroid&templateURL=https://raw.githubusercontent.com/serup-ai/mobiledroid/main/deploy/aws/cloudformation.yaml) |
| **DigitalOcean** | [![Deploy to DO](https://img.shields.io/badge/DigitalOcean-Create_Droplet-0080FF?logo=digitalocean)](https://m.do.co/c/c14767268755) |
| **Vultr** | [![Deploy on Vultr](https://img.shields.io/badge/Vultr-Deploy-007BFC?logo=vultr)](https://www.vultr.com/?ref=9853720) |

For more regions and detailed instructions, see [deploy/README.md](deploy/README.md).

## Features

- **AI Agent Control**: Natural language task execution on Android devices
- **Multi-Profile Management**: Create and manage multiple device profiles
- **Device Fingerprint Spoofing**: Antidetect capabilities with real device fingerprints
- **Per-Profile Proxy Support**: Residential IP compatibility per profile
- **Web-Based Control**: View and interact with devices via browser
- **Self-Hostable**: Docker, Docker Compose, Kubernetes support

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Linux host with kernel 5.4+ (for redroid KVM support)
- 8GB+ RAM recommended

### Setup

```bash
# Clone the repository
git clone https://github.com/serup.ai/mobiledroid.git
cd mobiledroid

# Copy environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env

# Start the platform
docker-compose -f docker/docker-compose.yml up -d

# Access the UI (default ports offset to avoid conflicts)
# UI:  http://<docker-host>:3100
# API: http://<docker-host>:8100
```

### Default Ports

| Service    | Port | Description           |
|------------|------|-----------------------|
| Web UI     | 3100 | Next.js frontend      |
| API        | 8100 | FastAPI backend       |
| ws-scrcpy  | 8186 | Device screen stream  |

Ports are configurable via environment variables (`UI_PORT`, `API_PORT`, `SCRCPY_PORT`).

### Kernel Modules (Required for redroid)

```bash
# Load required kernel modules
sudo modprobe binder_linux devices="binder,hwbinder,vndbinder"
sudo modprobe ashmem_linux
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Web UI (Next.js)                        │
│                    http://<host>:3100                       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                   API Server (FastAPI)                       │
│                    http://<host>:8100                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Profiles │ │ Devices  │ │  Tasks   │ │ Proxies  │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│                    AI Agent Service                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Vision  │ │ Planner  │ │ Actions  │ │   ADB    │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────┬───────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────┐
│              Device Containers (redroid)                     │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │Profile 1│ │Profile 2│ │Profile 3│ │Profile N│           │
│  │ Samsung │ │  Pixel  │ │ OnePlus │ │   ...   │           │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘           │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
mobiledroid/
├── docker/                     # Docker configurations
│   ├── Dockerfile.redroid      # Custom redroid with fingerprint injection
│   ├── Dockerfile.agent        # AI agent service
│   ├── Dockerfile.api          # Backend API
│   ├── Dockerfile.ui           # Next.js UI
│   └── docker-compose.yml      # Full stack compose
├── packages/
│   ├── agent/                  # AI agent (Python)
│   ├── api/                    # Backend API (FastAPI)
│   ├── ui/                     # Next.js frontend
│   └── shared/                 # Shared types/utils
├── config/
│   ├── fingerprints/           # Device fingerprint database
│   └── proxies.example.json    # Proxy configuration example
├── scripts/                    # Utility scripts
└── helm/                       # Kubernetes deployment
```

## Development

### Running Services Individually

```bash
# API Server
cd packages/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000

# UI
cd packages/ui
npm install
npm run dev

# Agent (typically runs within API context)
cd packages/agent
pip install -r requirements.txt
```

### API Documentation

Once the API is running, access:
- Swagger UI: http://<docker-host>:8100/docs
- ReDoc: http://<docker-host>:8100/redoc

## Configuration

### Device Fingerprints

Edit `config/fingerprints/devices.json` to add custom device profiles:

```json
{
  "id": "custom-device",
  "name": "Custom Device",
  "model": "MODEL-123",
  "brand": "brand",
  "manufacturer": "Manufacturer",
  "build_fingerprint": "...",
  "android_version": "13",
  "screen": {"width": 1080, "height": 2400, "dpi": 420}
}
```

### Proxy Configuration

Each profile can have its own proxy configuration:
- HTTP/HTTPS proxies
- SOCKS5 proxies
- Residential proxy support

## Community

- **Discord**: [Join our server](https://discord.gg/rP5PAjG3jx) - Get help, share feedback, connect with other users
- **Issues**: [GitHub Issues](https://github.com/serup-ai/mobiledroid/issues) - Report bugs or request features
- **Discussions**: [GitHub Discussions](https://github.com/serup-ai/mobiledroid/discussions) - Ask questions, share ideas

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
