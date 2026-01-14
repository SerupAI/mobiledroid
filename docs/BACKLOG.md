# Ditto Mobile Backlog

Prioritized list of features and improvements. Items marked with priority levels:
- **P0**: Critical - blocking launch
- **P1**: Important - needed for competitive parity
- **P2**: Nice to have - enhances product
- **P3**: Future - longer term improvements

---

## Phase 1: MVP (In Progress)

### Completed
- [x] Redis + Task Queue (arq worker)
- [x] Task Scheduling (datetime picker in UI)
- [x] Proxy per profile (HTTP/SOCKS5)
- [x] Enhanced fingerprinting (27+ params)
- [x] `/fingerprints/random` endpoint

### Remaining
- [ ] **P0**: Copy/paste clipboard support
- [ ] **P1**: MCP Server for external tool integration

---

## Fingerprinting Enhancements (P1)

To reach GeeLark parity (55+ params), implement these additional fingerprint parameters:

### Google Services IDs
- [ ] **GSF ID (Google Services Framework)** - Unique ID tied to Google account
  - Generate consistent ID per profile
  - Store in profile data for persistence
  - Set via `ro.boot.serialno` and GSF database

- [ ] **Google Advertising ID (GAID)** - Advertising identifier
  - Generate UUID v4 format
  - Persist across sessions
  - Allow reset functionality

### SafetyNet / Play Integrity
- [ ] **SafetyNet attestation responses** - Pass basic integrity checks
  - Research Redroid's SafetyNet bypass options
  - Consider Magisk/LSPosed integration
  - Document limitations

- [ ] **Play Integrity signals** - Newer replacement for SafetyNet
  - Device integrity verdict
  - Basic integrity checks
  - May require rooted device workarounds

### Sensor Fingerprinting
- [ ] **Accelerometer calibration data** - Unique per device
  - Generate realistic calibration offsets
  - Persist across sessions

- [ ] **Gyroscope data patterns** - Movement fingerprint
  - Randomize baseline noise
  - Device-specific characteristics

- [ ] **Magnetometer fingerprint** - Compass calibration
  - Generate unique calibration data

- [ ] **Sensor list fingerprint** - Available sensors
  - Match real device sensor lists
  - Include vendor-specific sensors

### Behavioral Fingerprinting
- [ ] **Battery level patterns** - Charging/discharging curves
  - Realistic drain rates
  - Charging speed variations
  - Battery health indicators

- [ ] **System uptime spoofing** - Boot time manipulation
  - Randomize boot timestamp
  - Realistic uptime progression

- [ ] **Touch timing patterns** - Human-like input
  - Variable touch duration
  - Realistic swipe velocities
  - Input jitter

### WebView Fingerprinting
- [ ] **Canvas fingerprint** - HTML5 canvas rendering
  - Device-specific rendering variations
  - Font rendering differences

- [ ] **WebGL fingerprint** - GPU rendering signature
  - Already have GL_RENDERER/GL_VENDOR
  - Add WebGL extensions list
  - Shader precision variations

- [ ] **Audio context fingerprint** - Audio processing signature
  - AudioContext.createOscillator variations
  - Sample rate differences

- [ ] **Font list fingerprint** - Installed fonts
  - Match real device font sets
  - Brand-specific fonts

### Network Fingerprinting
- [ ] **IMEI spoofing** - If applicable to use case
  - Generate valid IMEI checksums
  - Match device model patterns

- [ ] **SIM serial / ICCID** - SIM card identifiers
  - Format validation
  - Carrier-specific patterns

- [ ] **Network operator info** - MCC/MNC codes
  - Match proxy location
  - Realistic operator names

---

## Phase 2: SaaS Ready (P2)

### User Management
- [ ] User authentication (JWT)
- [ ] User registration / login
- [ ] Password reset flow
- [ ] Email verification

### Multi-tenancy
- [ ] Per-user profile isolation
- [ ] Usage quotas per user
- [ ] Role-based access control (admin/user)

### Billing
- [ ] Stripe integration
- [ ] Per-minute metering
- [ ] Usage dashboard
- [ ] Subscription plans
- [ ] Invoice generation

### Team Features
- [ ] Team/organization accounts
- [ ] Invite team members
- [ ] Shared device profiles
- [ ] Activity audit log

---

## Phase 3: Scale (P3)

### Infrastructure
- [ ] Kubernetes deployment
- [ ] Horizontal pod autoscaling
- [ ] Multi-region support
- [ ] Database replication

### Advanced Queue
- [ ] Priority queue lanes
- [ ] Parallel task execution
- [ ] Task dependencies
- [ ] Retry policies with backoff

### Enterprise
- [ ] SSO (SAML/OIDC)
- [ ] Audit logging
- [ ] Data export
- [ ] Custom SLAs

---

## Technical Debt

### Code Quality
- [ ] Add comprehensive test coverage
- [ ] API documentation (OpenAPI)
- [ ] Type hints throughout Python code
- [ ] Error handling improvements

### Performance
- [ ] Screenshot caching optimization
- [ ] WebSocket connection pooling
- [ ] Database query optimization
- [ ] Redis connection pooling

### DevOps
- [ ] GitHub Actions CI/CD
- [ ] Automated testing on PR
- [ ] Staging environment
- [ ] Blue-green deployments

---

## Ideas / Research

- [ ] **Voice commands** - Speech-to-text for device control
- [ ] **Screen recording** - Record automation sessions
- [ ] **Template library** - Pre-built automation templates
- [ ] **Browser extension** - Quick task creation from browser
- [ ] **Mobile app** - iOS/Android companion app
- [ ] **Webhook integrations** - Notify external systems on task completion

---

## How to Contribute

1. Pick an item from the backlog
2. Create a branch: `feature/item-name`
3. Implement with tests
4. Submit PR with description
5. Update this file when complete

---

*Last updated: January 2026*
