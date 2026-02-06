# Roadmap

> Track our progress and upcoming features. See [CONTRIBUTING.md](CONTRIBUTING.md) to help build these.

## Recently Shipped (v0.4.x)

- [x] AI agent with natural language control
- [x] Step limit approval flow
- [x] Quick app install panel
- [x] Task queue (Redis + arq)
- [x] Task scheduling
- [x] Proxy per profile (HTTP/SOCKS5)
- [x] 27+ parameter fingerprinting
- [x] Snapshot/restore profiles
- [x] One-click AWS/DO/Vultr deployment

---

## Open Source Roadmap

### Core Platform
- [ ] Copy/paste clipboard support
- [ ] Real-time screen view (ws-scrcpy)
- [ ] MCP Server for external integrations
- [ ] ARM/Graviton migration
- [ ] SSL/HTTPS setup guide
- [ ] S3/MinIO snapshot storage

### AI Agent
- [ ] Agent memory/context persistence
- [ ] Agent skill library (reusable sequences)
- [ ] Learned automations (AI generates scripts, auto-heals on failure)
- [ ] Agent scheduling (cron-based)
- [ ] Multi-agent orchestration
- [ ] Agent task queue with monitoring
- [ ] Multi-device coordination
- [ ] Advanced gesture recognition
- [ ] File system access
- [ ] Cross-app data transfer

### Proxy & Network
- [ ] BYOP (Bring Your Own Proxy) with rotation
- [ ] Proxy pool management API
- [ ] Hot-swap proxy (no restart)

### Antidetect Hardening
- [ ] Sensor spoofing (accelerometer, gyroscope, magnetometer)
- [ ] IMEI / hardware ID spoofing
- [ ] GSF ID / Google Advertising ID
- [ ] SafetyNet / Play Integrity research
- [ ] Battery & uptime spoofing
- [ ] Touch timing patterns
- [ ] Canvas / WebGL / Audio fingerprinting
- [ ] Font list fingerprint
- [ ] SIM serial / network operator

### Integrations
- [ ] OpenClaw (local LLM support)
- [ ] Claude Code skills.md
- [ ] Webhook notifications
- [ ] Voice commands
- [ ] Screen recording
- [ ] Template library
- [ ] Browser extension
- [ ] Mobile companion app

### Developer Experience
- [ ] GitHub Actions CI/CD
- [ ] Comprehensive test coverage
- [ ] Type hints throughout Python
- [ ] API documentation (OpenAPI)
- [ ] Kubernetes/Helm improvements

---

## Cloud Edition Only

*These features require managed infrastructure and are planned for [MobileDroid Cloud](https://mobiledroid-waitlist.conclusive-digital.workers.dev/?utm_source=github&utm_medium=readme&utm_campaign=oss).*

### User Management
- [ ] User authentication & accounts
- [ ] Team/organization accounts
- [ ] Role-based access control
- [ ] Shared device profiles

### Billing & Metering
- [ ] Per-minute usage metering
- [ ] Stripe integration
- [ ] Usage dashboard
- [ ] Subscription plans

### Scale & Enterprise
- [ ] Multi-region deployment
- [ ] Horizontal autoscaling
- [ ] Enterprise SSO (SAML/OIDC)
- [ ] Audit logging & compliance
- [ ] Custom SLAs

### Managed Proxies
- [ ] Residential proxy integration
- [ ] Pay-per-GB proxy billing

---

## Community

- [Discord](https://discord.gg/rP5PAjG3jx) - Get help, share feedback
- [GitHub Issues](https://github.com/serup-ai/mobiledroid/issues) - Report bugs
- [GitHub Discussions](https://github.com/serup-ai/mobiledroid/discussions) - Feature requests
