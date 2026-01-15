# CLAUDE.md - Ditto Mobile (MobileDroid)

AI-powered Android automation platform using Redroid containers for browser fingerprint management and mobile automation.

## Project Structure

```
ditto-mobile/
├── packages/
│   ├── api/          # FastAPI backend (Python 3.11)
│   └── ui/           # Next.js 14 frontend (React, TypeScript)
├── lib/
│   └── agent/        # AI agent for automation (Python)
├── docker/           # Docker Compose and Dockerfiles
├── infra/aws/        # Terraform for EC2 deployment
├── config/           # Fingerprint configs, proxy settings
└── scripts/          # Build and test scripts
```

## Architecture

- **API**: FastAPI with PostgreSQL, manages profiles and orchestrates Docker containers
- **UI**: Next.js with TanStack Query, provides device management interface
- **AI Agent**: Claude 4.5 Sonnet for natural language Android device control
- **Containers**: Redroid (Android in Docker) instances per profile
- **ADB**: Connects to containers via internal Docker network (`mobiledroid-{profile_id}:5555`)
- **ws-scrcpy**: Web-based screen mirroring (future real-time view)

## EC2 Deployment

The app runs on AWS EC2 at `34.235.77.142`.

### Deploy Code Changes

```bash
# Use the deploy script (captures git commit SHA)
./scripts/deploy-to-ec2.sh

# Or manually:
rsync -avz --exclude 'node_modules' --exclude '.next' --exclude '__pycache__' \
  --exclude 'venv' --exclude '.git' --exclude 'terraform.tfstate*' --exclude '*.pem' \
  -e "ssh -i infra/aws/mobiledroid-key.pem" \
  ./ ubuntu@34.235.77.142:/home/ubuntu/mobiledroid/

# SSH in and rebuild containers
ssh -i infra/aws/mobiledroid-key.pem ubuntu@34.235.77.142 \
  "cd /home/ubuntu/mobiledroid/docker && docker compose up -d --build"
```

### Access URLs

- **UI**: http://34.235.77.142:3100
- **API**: http://34.235.77.142:8100
- **API Docs**: http://34.235.77.142:8100/docs

### SSH Access

```bash
# Via Tailscale IP (preferred - works when exit node is active)
ssh -i infra/aws/mobiledroid-key.pem ubuntu@100.122.30.80

# Via public IP (may not work when exit node routes all traffic)
ssh -i infra/aws/mobiledroid-key.pem ubuntu@34.235.77.142
```

## Tailscale Exit Node (Residential IP)

EC2 is configured to route traffic through your home network via Tailscale for residential IP appearance.

### Current Setup
| Item | Value |
|------|-------|
| EC2 Tailscale IP | `100.122.30.80` |
| Exit Node | `desktop-tp59f6k` (Windows desktop) |
| Home/Residential IP | `76.49.30.63` |

### Tailscale Commands on EC2
```bash
# Check status
sudo tailscale status

# Verify current public IP (should be home IP)
curl ifconfig.me

# Change/set exit node
sudo tailscale up --exit-node=desktop-tp59f6k --accept-routes

# Disable exit node (revert to EC2's own IP)
sudo tailscale up --exit-node=
```

### If Exit Node Goes Offline
If Windows desktop goes offline, EC2 loses internet. Options:
1. Set up another exit node (e.g., Raspberry Pi at home)
2. Temporarily disable exit node: `sudo tailscale up --exit-node=`

### Connector API
```bash
# List all connectors
curl http://100.122.30.80:8100/connectors

# Check Tailscale connector status
curl http://100.122.30.80:8100/connectors/tailscale/status

# Get current public IP via API
curl http://100.122.30.80:8100/connectors/tailscale/ip
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
| `/chat/profiles/{id}` | POST | Send AI command to control device |
| `/chat/examples` | GET | Get example chat commands |
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

## AI Agent (Natural Language Device Control)

The MobileDroid AI Agent provides intelligent Android device automation through natural language commands using Claude 4.5 Sonnet.

### Quick Start

```bash
# Send a command to control the device
curl -X POST http://34.235.77.142:8100/chat/profiles/{profile_id} \
  -H "Content-Type: application/json" \
  -d '{"message": "Open the settings app and turn on airplane mode", "max_steps": 10}'
```

### How It Works

```
User Command → Chat API → Integration Service → AI Agent → Device Control
                                    ↓              ↓
                            Claude 4.5 AI ← Screenshot + UI Analysis
```

### Example Commands

**Simple Actions:**
- `"What do you see on the screen?"`
- `"Take a screenshot"`
- `"Click the back button"`
- `"Type 'hello world' in the text field"`

**Navigation:**
- `"Go to the home screen"`
- `"Open the settings app"`
- `"Swipe up to see all apps"`

**Complex Tasks:**
- `"Turn on airplane mode"`
- `"Set an alarm for 7 AM"`
- `"Send a message to John saying 'Hello'"`
- `"Install WhatsApp from the Play Store"`

### Chat API

**Request:**
```json
POST /chat/profiles/{profile_id}
{
  "message": "Your natural language command",
  "max_steps": 20
}
```

**Response:**
```json
{
  "success": true,
  "response": "I successfully turned on airplane mode by going to Settings > Network & Internet > Airplane mode and enabling the toggle.",
  "steps_taken": 5,
  "error": null
}
```

### Agent Architecture

**Components:**
- **Vision Service**: Screenshots + UI hierarchy analysis
- **Claude 4.5 AI**: Task understanding and action planning  
- **Action Executor**: Device control via ADB (tap, type, swipe, etc.)
- **Integration Service**: Database-driven LLM configuration

**Execution Flow:**
1. Capture device screenshot
2. Extract UI elements and coordinates
3. Send visual + text context to Claude AI
4. Parse AI response into device actions
5. Execute actions on Android device
6. Repeat until task complete

### Agent Configuration

The agent uses database-driven LLM configuration:
- **Provider**: Anthropic (Claude)
- **Model**: claude-sonnet-4-5-20250929
- **Max Steps**: Configurable per request (default: 20)
- **Temperature**: 0.0 (deterministic responses)

### Performance

**Timing Expectations:**
- Simple tasks (1-2 steps): 10-30 seconds
- Medium tasks (3-5 steps): 30-90 seconds
- Complex tasks (5+ steps): 2-5 minutes

**Capabilities:**
- Screenshot analysis and UI understanding
- Multi-step task automation
- Error recovery and retry logic
- Context-aware decision making

### Limitations

- No memory between separate chat sessions
- Single device control per request
- Limited to visible UI elements
- Text input requires on-screen keyboard

For detailed agent documentation, see [`lib/agent/README.md`](lib/agent/README.md).

## Environment Variables

Create `.env` in project root:
```bash
# Database
DATABASE_URL=postgresql+asyncpg://mobiledroid:mobiledroid@db:5432/mobiledroid

# API Keys (optional, for AI agent)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Debug mode (shows git commit SHA in UI)
DEBUG=true
NEXT_PUBLIC_DEBUG=true
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
- [ ] S3/MinIO integration for snapshot storage

### Debug Mode

When `DEBUG=true` and `NEXT_PUBLIC_DEBUG=true` are set:
- Git commit SHA is displayed in bottom-left corner of UI
- API health endpoint includes commit SHA
- Build timestamp is shown in UI

### Resolved Issues

- **ADB not connecting**: Fixed by using container names instead of `localhost:{port}` and ensuring all containers are on the same Docker network
- **"Failed to fetch" on start**: Fixed by making start async - returns immediately, UI polls `/ready` endpoint
- **Boot progress not visible**: Fixed by updating `check_ready` to work during "starting" state and auto-transition to "running"

## File Locations

### Core Services
- **Profile Service**: `packages/api/src/services/profile_service.py`
- **Docker Service**: `packages/api/src/services/docker_service.py`
- **ADB Service**: `packages/api/src/services/adb_service.py`
- **Integration Service**: `packages/api/src/services/integration_service.py`

### API Routers  
- **Profile Router**: `packages/api/src/routers/profiles.py`
- **Chat Router**: `packages/api/src/routers/chat.py`

### AI Agent
- **Main Agent**: `lib/agent/src/agent.py`
- **Vision Service**: `lib/agent/src/vision.py`
- **Action Executor**: `lib/agent/src/actions.py`
- **Agent Wrapper**: `packages/api/src/agent_wrapper.py`

### Frontend
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
