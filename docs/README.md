# MobileDroid Documentation

Comprehensive documentation for the MobileDroid AI-powered Android automation platform.

## Documentation Index

### 📚 **Main Documentation**
- **[CLAUDE.md](../CLAUDE.md)** - Primary project documentation with overview, deployment, and usage
- **[lib/agent/README.md](../lib/agent/README.md)** - Detailed AI agent architecture and development guide

### 🤖 **AI Agent Documentation**
- **[Chat API Reference](chat-api.md)** - Complete API documentation with examples and integration guides

## Quick Navigation

### Getting Started
1. **Project Overview** → [CLAUDE.md](../CLAUDE.md) - Start here for project introduction
2. **Agent Usage** → [Chat API](chat-api.md) - Learn how to control devices with natural language
3. **Agent Development** → [Agent README](../lib/agent/README.md) - Technical details and customization

### Key Features

#### 🎮 **Device Control**
- Natural language commands for Android automation
- Real-time screen streaming and interaction
- Multi-step task execution with AI reasoning

#### 🏗️ **Architecture**
- FastAPI backend with PostgreSQL
- Next.js frontend with real-time updates
- Claude 4.5 Sonnet AI integration
- Docker containerized Android devices

#### 🚀 **Deployment**
- AWS EC2 production deployment
- Local development with Docker
- Automated build and deploy scripts

## Example Usage

### Basic Device Control
```bash
# Send natural language command to device
curl -X POST http://34.235.77.142:8100/chat/profiles/{profile_id} \
  -H "Content-Type: application/json" \
  -d '{"message": "Open settings and turn on airplane mode"}'
```

### Agent Integration
```python
from lib.agent.src.agent import MobileDroidAgent

agent = await MobileDroidAgent.connect("device-host", 5555, api_key)
result = await agent.execute_task("Take a screenshot and describe what you see")
```

## Documentation Structure

```
docs/
├── README.md          # This overview document
├── chat-api.md        # Chat API reference and examples
../CLAUDE.md           # Main project documentation  
../lib/agent/README.md # Agent architecture and development
```

## Development Documentation

### Core Components
- **API Services** - Profile, Docker, ADB, Integration services
- **AI Agent** - Vision, Action execution, Claude integration
- **Frontend** - Device viewer, profile management, real-time updates
- **Infrastructure** - Docker, AWS deployment, networking

### Key Technologies
- **Backend**: Python 3.11, FastAPI, PostgreSQL, SQLAlchemy
- **Frontend**: Next.js 14, React, TypeScript, TanStack Query
- **AI**: Claude 4.5 Sonnet, Computer Vision, Natural Language Processing
- **Android**: Redroid containers, ADB automation, UI hierarchy analysis
- **Infrastructure**: Docker, AWS EC2, Terraform

## Contributing

### Documentation Updates
1. **Main features** → Update [CLAUDE.md](../CLAUDE.md)
2. **AI agent changes** → Update [lib/agent/README.md](../lib/agent/README.md)
3. **API changes** → Update [chat-api.md](chat-api.md)
4. **New features** → Add documentation to appropriate section

### Code Documentation
- Include comprehensive docstrings for all functions
- Add type hints for better IDE support
- Update README files when adding new components
- Document environment variables and configuration

## Support

For technical issues and questions:
1. Check the relevant documentation section above
2. Review example usage in each documentation file
3. Examine the codebase for implementation details

## Version Information

This documentation corresponds to:
- **Project Version**: 0.1.0
- **Agent Location**: `lib/agent/` (moved from `packages/agent/`)
- **Claude Model**: claude-sonnet-4-5-20250929
- **Database**: PostgreSQL with SQLAlchemy async support
- **Deployment**: AWS EC2 with Docker Compose

Last Updated: January 2026