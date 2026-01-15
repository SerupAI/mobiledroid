# Security Policy

## Supported Versions

We release patches for security vulnerabilities for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

1. **Do NOT** open a public GitHub issue for security vulnerabilities
2. Email security concerns to: **security@serup.ai**
3. Include as much detail as possible:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: We will acknowledge receipt within 48 hours
- **Initial Assessment**: We will provide an initial assessment within 7 days
- **Resolution Timeline**: Critical vulnerabilities will be addressed within 30 days
- **Disclosure**: We practice coordinated disclosure and will work with you on timing

### Bug Bounty

We do not currently have a formal bug bounty program, but we deeply appreciate security researchers who report vulnerabilities responsibly. Contributors may be acknowledged in our release notes (with permission).

## Security Measures

### Code Security

- **Static Analysis**: CodeQL scans on all pull requests
- **Secret Detection**: Gitleaks scans to prevent credential leaks
- **Dependency Scanning**: Dependabot monitors for vulnerable dependencies

### Container Security

- Non-root users in production containers
- Minimal base images (slim/alpine variants)
- Regular base image updates via Dependabot

### Runtime Security

- All API endpoints require appropriate authentication (when enabled)
- ADB connections are restricted to the internal Docker network
- Redroid containers are isolated with configurable resource limits

## Security Best Practices for Deployment

### Production Deployment

1. **Never expose ADB ports** (5555+) to the public internet
2. **Use a reverse proxy** (nginx/traefik) with SSL/TLS
3. **Enable authentication** for the API endpoints
4. **Restrict network access** using firewall rules
5. **Use secrets management** for API keys and credentials

### Environment Variables

Never commit secrets to the repository. Use environment variables or secrets management:

```bash
# Good - Use environment variables
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://...

# Bad - Never hardcode in source files
```

### Docker Security

```yaml
# Recommended docker-compose security settings
services:
  api:
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp
```

## Known Security Considerations

### Redroid Containers

Redroid containers require privileged mode or specific capabilities to function. This is a known requirement of Android emulation. Mitigations:

- Run on dedicated hosts, not shared infrastructure
- Use network isolation between Redroid instances
- Limit container resource usage

### ADB Access

ADB provides full device control. Protect ADB access by:

- Never exposing ADB ports externally
- Using Docker network isolation
- Implementing API-level access controls

## Security Updates

Security updates are released as patch versions. Subscribe to GitHub releases to be notified of security patches.

---

Thank you for helping keep MobileDroid and its users safe!
