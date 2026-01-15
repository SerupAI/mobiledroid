# Fingerprint & Evasion Matrix

**Status**: MobileDroid vs GeLark comparison
**Last Updated**: January 2026

## Summary

| Metric | MobileDroid | GeLark |
|--------|:-----------:|:------:|
| **Parameters** | 27 | 55+ |
| **Core Evasion** | 70% | 95% |
| **Browser Detection** | Basic | Full |
| **Google Services** | Partial | Full |
| **Sensor Spoof** | None | Full |

---

## Feature Matrix

### Legend
- ✅ Implemented
- ⚠️ Partial
- ❌ Not implemented
- **Core** = Open source feature
- **SaaS** = Premium/SaaS-only feature

---

### Device Identity

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| Model/Brand/Manufacturer | ✅ | ✅ | Core | Done | `ro.product.*` props |
| Device/Product name | ✅ | ✅ | Core | Done | |
| Build fingerprint (6 variants) | ✅ | ✅ | Core | Done | All build.fingerprint props |
| Serial number | ✅ | ✅ | Core | Done | `ro.serialno`, `ro.boot.serialno` |
| Android ID | ✅ | ✅ | Core | Done | `Settings.Secure.ANDROID_ID` |

### Build Information

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| SDK version | ✅ | ✅ | Core | Done | |
| Android version | ✅ | ✅ | Core | Done | |
| Build incremental | ✅ | ✅ | Core | Done | |
| Build type/tags | ✅ | ✅ | Core | Done | user/release-keys |
| Build ID/display | ✅ | ✅ | Core | Done | |

### Hardware

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| Board/platform | ✅ | ✅ | Core | Done | `ro.board.platform` |
| CPU ABI | ✅ | ✅ | Core | Done | arm64-v8a |
| Bootloader | ✅ | ✅ | Core | Done | |
| Hardware name | ✅ | ✅ | Core | Done | `ro.hardware` |

### Display

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| Screen resolution | ✅ | ✅ | Core | Done | width x height |
| DPI/density | ✅ | ✅ | Core | Done | `ro.sf.lcd_density` |
| Refresh rate | ✅ | ✅ | Core | Done | 60/90/120Hz |

### Graphics

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| GL Renderer | ✅ | ✅ | Core | Done | Adreno/Mali |
| GL Vendor | ✅ | ✅ | Core | Done | Qualcomm/ARM |
| OpenGL version | ✅ | ✅ | Core | Done | |
| **WebGL fingerprint** | ❌ | ✅ | Core | **P1** | Browser detection |
| **Canvas fingerprint** | ❌ | ✅ | Core | **P1** | Browser detection |
| WebGL extensions | ❌ | ✅ | SaaS | P2 | |

### Network

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| WiFi MAC address | ✅ | ✅ | Core | Done | Prefix per device |
| Bluetooth MAC | ✅ | ✅ | Core | Done | |
| IMEI spoofing | ❌ | ✅ | SaaS | P2 | Carrier detection |
| SIM serial/ICCID | ❌ | ✅ | SaaS | P2 | |
| MCC/MNC codes | ❌ | ✅ | SaaS | P2 | Network operator |
| Phone number | ❌ | ✅ | SaaS | P3 | |

### Locale & Region

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| Timezone | ✅ | ✅ | Core | Done | America/New_York |
| Language | ✅ | ✅ | Core | Done | en |
| Region/Country | ✅ | ✅ | Core | Done | US |
| Locale | ✅ | ✅ | Core | Done | en_US |

### Google Services

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| **GSF ID** | ❌ | ✅ | Core | **P1** | Google Services Framework ID |
| **GAID** | ❌ | ✅ | Core | **P1** | Google Advertising ID |
| SafetyNet attestation | ❌ | ✅ | SaaS | P2 | Basic integrity |
| Play Integrity | ❌ | ✅ | SaaS | P2 | Newer API |

### Sensors

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| Accelerometer calibration | ❌ | ✅ | SaaS | P2 | Unique per device |
| Gyroscope fingerprint | ❌ | ✅ | SaaS | P2 | Movement patterns |
| Magnetometer | ❌ | ✅ | SaaS | P3 | |
| Sensor list spoof | ❌ | ✅ | SaaS | P2 | Available sensors |

### Behavioral

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| **System uptime** | ❌ | ✅ | Core | **P1** | Boot time spoof |
| Battery patterns | ❌ | ✅ | SaaS | P3 | Drain/charge curves |
| Touch timing | ❌ | ✅ | SaaS | P2 | Human-like input |

### Anti-Emulator

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| Hide qemu/virtual | ✅ | ✅ | Core | Done | `ro.kernel.qemu=0` |
| Baseband version | ✅ | ✅ | Core | Done | Real baseband string |
| RIL version | ✅ | ✅ | Core | Done | |
| Emulator detection bypass | ⚠️ | ✅ | Core | P1 | Some apps still detect |

### Vendor-Specific

| Feature | MobileDroid | GeLark | Tier | Priority | Notes |
|---------|:-----------:|:------:|:----:|:--------:|-------|
| Samsung Knox props | ✅ | ✅ | Core | Done | |
| Google GMS version | ✅ | ✅ | Core | Done | |
| Xiaomi MIUI props | ✅ | ✅ | Core | Done | |
| OnePlus Oxygen props | ✅ | ✅ | Core | Done | |
| OPPO/Vivo/Honor | ✅ | ✅ | Core | Done | |

---

## P1 Implementation Plan (Core)

These are critical for avoiding detection on major platforms:

### 1. GSF ID (Google Services Framework)
- Unique ID tied to Google account
- Required for Play Store apps
- Persist per profile

### 2. GAID (Google Advertising ID)
- UUID v4 format
- Used by ad SDKs for tracking
- Should be resettable

### 3. WebGL Fingerprint
- GPU rendering signature
- Detected by browser-based checks
- Match real device WebGL output

### 4. Canvas Fingerprint
- HTML5 canvas rendering variations
- Font rendering differences
- Device-specific patterns

### 5. System Uptime Spoofing
- Boot timestamp manipulation
- Realistic uptime progression
- Avoid "just rebooted" detection

---

## Detection Risk by Platform

| Platform | Risk Level | Key Checks | MobileDroid Status |
|----------|:----------:|------------|:------------------:|
| **Instagram** | High | Device linking, IP, behavior | ⚠️ Needs P1 |
| **TikTok** | Very High | SafetyNet, sensors, timing | ⚠️ Needs P1+P2 |
| **Threads** | High | Same as Instagram | ⚠️ Needs P1 |
| **Twitter/X** | Medium | Basic device check | ✅ OK |
| **Facebook** | High | Device graph, IP linking | ⚠️ Needs P1 |
| **LinkedIn** | Medium | Basic checks | ✅ OK |
| **Reddit** | Low | Minimal detection | ✅ OK |

---

## Proxy/IP Considerations

Even with perfect fingerprinting, IP address matters:

| IP Type | Detection Risk | Recommendation |
|---------|:--------------:|----------------|
| Datacenter IP | Very High | Avoid |
| Residential proxy | Low | Good option |
| Mobile proxy | Very Low | Best option |
| **Tailscale exit node** | Very Low | Same IP as real phone |

**Recommended Setup**: Use Tailscale exit node from home network so emulated device shares IP with real phone.

---

## Files Reference

- **Fingerprint configs**: `config/fingerprints/devices.json`
- **Fingerprint service**: `packages/api/src/services/fingerprint_service.py`
- **Fingerprint router**: `packages/api/src/routers/fingerprints.py`
- **Device schemas**: `packages/api/src/schemas/profile.py`

---

*Last updated: January 2026*
