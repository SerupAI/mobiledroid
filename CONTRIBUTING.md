# Contributing to MobileDroid

Thank you for your interest in contributing to MobileDroid! This document provides guidelines for contributing.

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Linux host with kernel 5.4+ (for redroid KVM support)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/serup-ai/mobiledroid.git
cd mobiledroid

# Copy environment file
cp .env.example .env
# Edit .env with your API keys

# Start services
docker-compose -f docker/docker-compose.yml up -d

# Run API locally (for development)
cd packages/api
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
uvicorn src.main:app --reload --port 8000

# Run UI locally
cd packages/ui
npm install
npm run dev
```

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs
- Include steps to reproduce
- Include environment details (OS, Docker version, etc.)
- Include relevant logs

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Run tests: `cd packages/api && pytest tests/ -v`
5. Commit with clear messages
6. Push to your fork
7. Open a Pull Request

### Code Style

**Python:**
- Follow PEP 8
- Use type hints
- Run `black` for formatting
- Run `ruff` for linting

**TypeScript:**
- Use TypeScript strict mode
- Follow existing patterns in codebase
- Run `npm run lint`

### Testing

All PRs should include tests where applicable:

```bash
# Run all tests
cd packages/api
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=term-missing
```

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Questions?

- Open a GitHub Discussion
- Join our community (links TBD)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
