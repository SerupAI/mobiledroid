# CLAUDE.md - Ditto Mobile (MobileDroid)

AI-powered Android automation platform using Redroid containers for browser fingerprint management and mobile automation.

## Project Structure

```
ditto-mobile/
├── packages/
│   ├── api/          # FastAPI backend (Python 3.11)
│   ├── ui/           # Next.js 14 frontend (React, TypeScript)
│   └── agent/        # AI agent for automation (Python)
├── docker/           # Docker Compose and Dockerfiles
├── infra/aws/        # Terraform for EC2 deployment
├── config/           # Fingerprint configs, proxy settings
└── scripts/          # Build and test scripts
```

## Architecture

- **API**: FastAPI with PostgreSQL, manages profiles and orchestrates Docker containers
- **UI**: Next.js with TanStack Query, provides device management interface
- **Containers**: Redroid (Android in Docker) instances per profile
- **ADB**: Connects to containers via internal Docker network (`mobiledroid-{profile_id}:5555`)
- **ws-scrcpy**: Web-based screen mirroring (future real-time view)

## EC2 Deployment

The app runs on AWS EC2 at `34.235.77.142`.

### Deploy Code Changes

```bash
# 1. Rsync code to EC2
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' \
  --exclude 'venv' --exclude '.git' --exclude 'terraform.tfstate*' --exclude '*.pem' \
  -e "ssh -i infra/aws/mobiledroid-key.pem" \
  ./ ubuntu@34.235.77.142:/home/ubuntu/mobiledroid/

# 2. SSH in and rebuild containers
ssh -i infra/aws/mobiledroid-key.pem ubuntu@34.235.77.142 \
  "cd /home/ubuntu/mobiledroid/docker && docker compose up -d --build"
```

### Access URLs

- **UI**: http://34.235.77.142:3100
- **API**: http://34.235.77.142:8100
- **API Docs**: http://34.235.77.142:8100/docs

### SSH Access

```bash
ssh -i infra/aws/mobiledroid-key.pem ubuntu@34.235.77.142
```

## Local Development

### Using Local Docker (192.168.1.26)

```bash
export DOCKER_HOST=ssh://adrna@192.168.1.26
cd docker && docker compose up -d --build
```

### Run Tests

```bash
cd packages/api
python -m pytest tests/ -v --cov=src
```

## Key API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/profiles` | GET | List all profiles |
| `/profiles` | POST | Create new profile |
| `/profiles/{id}/start` | POST | Start profile (async, returns immediately) |
| `/profiles/{id}/stop` | POST | Stop profile |
| `/profiles/{id}/ready` | GET | Check boot progress (poll this after start) |
| `/profiles/{id}/screenshot` | GET | Get device screenshot |
| `/fingerprints/random` | GET | Generate random device fingerprint |

## Profile Lifecycle

1. **Create**: `POST /profiles` with name and fingerprint
2. **Start**: `POST /profiles/{id}/start` - returns immediately with status "starting"
3. **Poll Ready**: `GET /profiles/{id}/ready` - returns:
   - `container_running`: Docker container is up
   - `adb_connected`: ADB connected to device
   - `screen_available`: Screenshot can be taken
   - `ready`: All checks passed, device ready for interaction
4. **View**: Once ready, screenshots available at `/profiles/{id}/screenshot`
5. **Stop**: `POST /profiles/{id}/stop`

## Docker Networking

Containers communicate via `mobiledroid_network`. ADB addresses use container names:
- Container name: `mobiledroid-{profile_id}`
- ADB address: `mobiledroid-{profile_id}:5555`

The network is explicitly named in docker-compose.yml to avoid prefix issues:
```yaml
networks:
  mobiledroid_network:
    name: mobiledroid_network
    driver: bridge
```

## Environment Variables

Create `.env` in project root:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://mobiledroid:mobiledroid@db:5432/mobiledroid

# API Keys (optional, for AI agent)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Terraform (AWS Infrastructure)

```bash
cd infra/aws

# Initialize
terraform init

# Plan changes
terraform plan

# Apply
terraform apply

# Get outputs
terraform output
```

Security group restricts access to:
- Your public IP: `76.49.30.63/32`
- Tailscale IP: `100.110.85.54/32`

## Known Issues & TODOs

### Pending Work

- [ ] Real-time screen view using ws-scrcpy instead of screenshot polling
- [ ] Proxy configuration for containers
- [ ] Multi-tenancy and user authentication
- [ ] GitHub Actions CI/CD pipeline
- [ ] SSL/HTTPS setup with Let's Encrypt

### Resolved Issues

- **ADB not connecting**: Fixed by using container names instead of `localhost:{port}` and ensuring all containers are on the same Docker network
- **"Failed to fetch" on start**: Fixed by making start async - returns immediately, UI polls `/ready` endpoint
- **Boot progress not visible**: Fixed by updating `check_ready` to work during "starting" state and auto-transition to "running"

## File Locations

- **Profile Service**: `packages/api/src/services/profile_service.py`
- **Docker Service**: `packages/api/src/services/docker_service.py`
- **ADB Service**: `packages/api/src/services/adb_service.py`
- **Profile Router**: `packages/api/src/routers/profiles.py`
- **Device Viewer**: `packages/ui/components/DeviceViewer.tsx`
- **Profile Card**: `packages/ui/components/ProfileCard.tsx`
- **API Client**: `packages/ui/lib/api.ts`

## Git

```bash
# Commit changes
git add -A
git commit -m "Description of changes"

# Push to GitHub (once remote is set up)
git push origin main
```
