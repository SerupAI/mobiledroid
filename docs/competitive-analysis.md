# Competitive Analysis: Ditto vs GeeLark

**Last Updated:** January 2026

## Executive Summary

| Aspect | GeeLark | Ditto |
|--------|---------|-------|
| **Target user** | Developers, scripters | Non-technical, AI-first |
| **Automation method** | Code (Puppeteer/Selenium/RPA) | Natural language |
| **Learning curve** | High (need to code) | Low (just describe task) |
| **Flexibility** | High (full code control) | Medium (AI interprets) |
| **Price point** | Low ($0.007/min) | Higher (AI costs) |
| **Unique value** | Cheap, scriptable | AI brain, no-code |

---

## Feature Comparison

### What Ditto HAS (Advantages)

| Feature | Status | Notes |
|---------|--------|-------|
| **AI Agent** | ✅ Working | Natural language → device control. GeeLark doesn't have this. |
| **WebSocket streaming** | ✅ Working | Real-time ~30fps screen view |
| **Snapshot/restore** | ✅ Working | Save and restore device states |
| **Chat interface** | ✅ Working | Conversational device control |
| **Session history** | ✅ Working | Replay past agent sessions |
| **ADB integration** | ✅ Working | Tap, swipe, type, keys |
| **Profile management** | ✅ Working | Create, start, stop devices |
| **Task queue** | ✅ Working | Redis-based queue with arq worker |
| **Task scheduling** | ✅ Working | Schedule tasks for future execution |
| **Proxy per profile** | ✅ Working | HTTP/SOCKS5 proxy support per device |
| **Fingerprinting** | ✅ 27+ params | Device ID, build, hardware, network, locale, vendor-specific |

### What Ditto is MISSING (Gaps)

| Feature | GeeLark | Ditto | Priority |
|---------|---------|-------|----------|
| **Proxy per device** | ✅ | ✅ | ~~P0~~ Done |
| **Task queue** | ✅ | ✅ | ~~P0~~ Done |
| **Task scheduling** | ✅ | ✅ | ~~P0~~ Done |
| **Per-minute metering** | ✅ | ❌ | P2 |
| **55+ fingerprint params** | ✅ | ⚠️ 27 params | P1 - In Progress |
| **Puppeteer/Selenium API** | ✅ | ❌ | P1 (MCP covers this) |
| **User auth / accounts** | ✅ | ❌ | P2 |
| **Team collaboration** | ✅ | ❌ | P2 |
| **Billing / Stripe** | ✅ | ❌ | P2 |
| **RPA templates** | ✅ | ❌ | P3 (AI replaces need) |

---

## GeeLark Details

**Website:** https://www.geelark.com

**Pricing:**
- Per-minute: $0.007/min
- Daily cap: $1/day
- Monthly rental: $29.9/mo unlimited
- Free trial available

**Key Features:**
- Real Android cloud devices
- 55+ parameter fingerprint spoofing
- Puppeteer, Selenium, Postman automation support
- RPA (Robotic Process Automation) templates
- Profile management (local and cloud)
- Team access / collaboration
- GDPR compliant, 2FA security

**Target Use Cases:**
- Multi-account management
- Social media automation
- App testing
- Team-based Android device operations

---

## Fingerprint Comparison

### Ditto (Current - 27 Parameters)

```
Parameters we spoof:

DEVICE IDENTITY (10)
- ro.product.model
- ro.product.brand
- ro.product.manufacturer
- ro.product.name
- ro.product.device
- ro.product.system.* (model, brand, manufacturer)
- ro.product.vendor.* (model, brand)

BUILD FINGERPRINT (6)
- ro.build.fingerprint
- ro.bootimage.build.fingerprint
- ro.system.build.fingerprint
- ro.vendor.build.fingerprint
- ro.odm.build.fingerprint
- ro.product.build.fingerprint

BUILD INFO (8)
- ro.build.id
- ro.build.display.id
- ro.build.version.incremental
- ro.build.type
- ro.build.tags
- ro.build.version.sdk
- ro.build.version.release
- ro.build.version.release_or_codename

HARDWARE (8)
- ro.hardware
- ro.product.board
- ro.board.platform
- ro.bootloader
- ro.boot.hardware
- ro.product.cpu.abi
- ro.product.cpu.abilist
- ro.product.cpu.abilist64/32

SERIAL NUMBER (3)
- ro.serialno
- ro.boot.serialno
- ro.hardware.serial

DISPLAY (4)
- ro.sf.lcd_density
- ro.product.display_size
- ro.surface_flinger.max_frame_buffer_acquired_buffers
- ro.surface_flinger.refresh_rate_switching

GRAPHICS (3)
- ro.hardware.egl
- ro.opengles.version
- debug.hwui.renderer

NETWORK (4)
- ro.boot.wifimacaddr
- persist.wifi.macaddr
- ro.boot.btmacaddr
- persist.bluetooth.macaddr

LOCALE (5)
- persist.sys.timezone
- persist.sys.locale
- ro.product.locale
- persist.sys.language
- persist.sys.country

VENDOR-SPECIFIC (varies by brand)
- Samsung: knox, omc
- Google: gmsversion, hardware.revision
- OnePlus: oxygen version
- Xiaomi: miui version/region
- OPPO/Vivo/Honor/Realme variants

ANTI-EMULATOR (5)
- ro.kernel.qemu
- ro.hardware.virtual
- ro.product.cpu.abilist
- gsm.version.baseband
- gsm.version.ril-impl

Total: 27+ core parameters + vendor-specific
```

### GeeLark (Advanced - 55+ Parameters)

```
Parameters they likely spoof:

DEVICE IDENTITY
- ro.product.model
- ro.product.brand
- ro.product.manufacturer
- ro.product.device
- ro.product.name
- ro.product.board
- ro.hardware
- ro.bootloader
- ro.serialno
- Settings.Secure.ANDROID_ID

BUILD INFO
- ro.build.fingerprint
- ro.build.id
- ro.build.display.id
- ro.build.version.incremental
- ro.build.version.sdk
- ro.build.version.release
- ro.build.type
- ro.build.tags
- ro.build.host
- ro.build.user

HARDWARE
- ro.board.platform
- ro.arch
- CPU ABI
- CPU ABI2
- Supported ABIs list
- Hardware serial
- Bootloader version

SCREEN & DISPLAY
- Screen width/height
- Screen DPI
- Display density
- Refresh rate
- HDR capabilities
- Wide color gamut

SENSORS (if present)
- Accelerometer calibration
- Gyroscope data
- Magnetometer
- Sensor list fingerprint

NETWORK
- MAC address (WiFi)
- Bluetooth MAC
- IMEI (if applicable)
- IMSI
- SIM serial
- Phone number
- Network operator
- MCC/MNC codes

WEBVIEW / BROWSER
- WebView user agent
- WebGL renderer
- WebGL vendor
- Canvas fingerprint
- Audio context fingerprint
- Font list
- Plugin list

SYSTEM
- Timezone
- Locale
- Language
- Keyboard
- Input methods
- Installed apps hash
- System uptime
- Battery level patterns

GOOGLE SERVICES
- GSF ID (Google Services Framework)
- Google Advertising ID
- SafetyNet attestation responses
- Play Integrity signals

Total: 55-80+ parameters
```

### Why This Matters

Social media platforms (Instagram, TikTok, etc.) use fingerprinting to detect:
1. **Emulator detection** - Is this a real device?
2. **Device linking** - Are multiple accounts on same device?
3. **Bot detection** - Unusual sensor/timing patterns

With only 10 parameters, Ditto devices may be:
- Flagged as emulators
- Linked across accounts
- Rate-limited or banned

---

## Pricing Strategy

### Cost Comparison

| Tier | GeeLark | Ditto (Suggested) | Justification |
|------|---------|-------------------|---------------|
| Per-minute | $0.007 | $0.02-0.05 | AI API costs + no-code value |
| Daily cap | $1/day | $3-5/day | Premium positioning |
| Monthly | $29.9 unlimited | $49-99 with limits | Higher value tier |

### Margin Analysis

```
GeeLark per-minute breakdown (estimated):
- Infrastructure: $0.003
- Margin: $0.004
- Gross margin: ~57%

Ditto per-minute breakdown (estimated):
- Infrastructure: $0.003
- Claude API: $0.005-0.02 (varies by task complexity)
- Margin: $0.01-0.02
- Gross margin: ~40-50%
```

---

## Competitive Position

### GeeLark Strengths
- Established player
- Very low pricing
- Comprehensive fingerprinting
- Selenium/Puppeteer ecosystem integration
- RPA templates library

### GeeLark Weaknesses
- Requires coding knowledge
- No AI/natural language
- Users must build automations manually
- Learning curve for non-developers

### Ditto Strengths
- AI-powered (unique differentiator)
- Natural language commands
- No coding required
- Snapshot/restore workflow
- Open source potential (community)

### Ditto Weaknesses
- Missing table-stakes features (proxy, scheduling)
- Basic fingerprinting
- Higher operational costs (AI)
- No user auth/billing yet

---

## Roadmap to Competitive Parity

### Phase 1: MVP (4-6 weeks)
**Goal:** Basic feature parity for power users

- [x] P0: Redis + Task Queue ✅ (arq worker with task queue)
- [x] P0: Task Scheduling ✅ (datetime picker in UI)
- [x] P0: Proxy per profile ✅ (proxy pool implemented)
- [ ] P0: Copy/paste clipboard
- [x] P1: Enhanced fingerprinting (25+ params) ✅ (27 params now)
- [ ] P1: MCP Server

### Phase 2: SaaS Ready (8-12 weeks)
**Goal:** Multi-tenant, billable product

- [ ] P2: User authentication
- [ ] P2: Per-minute metering
- [ ] P2: Stripe billing integration
- [ ] P2: Team/collaboration features
- [ ] P2: Full fingerprinting (55+ params)

### Phase 3: Scale (12+ weeks)
**Goal:** Production-grade infrastructure

- [ ] P3: Kubernetes deployment
- [ ] P3: Multi-region support
- [ ] P3: Advanced queue (priorities, parallel)
- [ ] P3: Enterprise features (SSO, audit)

---

## Key Takeaways

1. **Our moat is AI** - GeeLark makes users write code; we let them talk to their phone
2. ~~**Missing table stakes**~~ - ✅ Proxy and scheduling now implemented!
3. **Fingerprinting improving** - Now 27+ params (up from 10), approaching parity with GeeLark's 55+
4. **Price premium justified** - AI value supports 3-7x pricing vs GeeLark
5. **Open source opportunity** - GeeLark is closed; OSS core could drive adoption
6. **Phase 1 nearly complete** - Only clipboard and MCP server remaining for MVP

---

## References

- GeeLark Website: https://www.geelark.com
- GeeLark Pricing: https://www.geelark.com/pricing/
- Cloud Phone Comparison: https://pixelscan.net/blog/best-cloud-phone-android-providers/
