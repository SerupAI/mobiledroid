# MobileDroid Architecture

## Overview

MobileDroid is an AI-powered Android automation platform using Redroid containers with comprehensive device fingerprinting.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Next.js / React / TanStack)                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API Layer                              │
│                    (FastAPI / Python 3.11)                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐    │
│  │ Profiles │  │   Chat   │  │Fingerprnt│  │    Tasks     │    │
│  │  Router  │  │  Router  │  │  Router  │  │   Router     │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘    │
└─────────────────────────────┬───────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Docker    │      │  AI Agent   │      │ Fingerprint │
│   Service   │      │  (Claude)   │      │   Service   │
└──────┬──────┘      └──────┬──────┘      └─────────────┘
       │                    │
       ▼                    ▼
┌─────────────┐      ┌─────────────┐
│   Redroid   │◄─────│     ADB     │
│  Container  │      │   Service   │
└─────────────┘      └─────────────┘
```

---

## AI-Generated RPA System (Operator Pattern)

### Concept

Traditional RPA requires manual script creation. Our system uses AI to **generate RPA scripts automatically** during first execution, then caches them for fast, cost-free subsequent runs.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Task Request                              │
│              "Open Instagram and like 3 posts"                   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                       ┌──────▼──────┐
                       │ Orchestrator │
                       │    Agent     │
                       └──────┬──────┘
                              │
               ┌──────────────┼──────────────┐
               │              │              │
               ▼              ▼              ▼
        ┌───────────┐  ┌───────────┐  ┌───────────┐
        │  Explicit │  │   Cache   │  │    No     │
        │  Override │  │   Match   │  │   Match   │
        │           │  │           │  │  (New)    │
        └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
              │              │              │
              ▼              ▼              ▼
        ┌───────────┐  ┌───────────┐  ┌───────────┐
        │  Execute  │  │  Execute  │  │  Builder  │
        │ Specified │  │  Cached   │  │   Agent   │
        │    RPA    │  │    RPA    │  │           │
        └───────────┘  └─────┬─────┘  └─────┬─────┘
                             │              │
                             │         AI executes task
                             │         while recording
                             │         all actions
                             │              │
                             │         ┌────▼─────┐
                             │         │  Save    │
                             │         │  RPA     │
                             │         │  Script  │
                             │         └──────────┘
                             │
                       ┌─────▼─────┐
                       │  Success? │
                       └─────┬─────┘
                             │
                    ┌────────┴────────┐
                    │ Yes             │ No (Error)
                    ▼                 ▼
                  Done         ┌───────────┐
                               │ Recovery  │
                               │   Agent   │
                               └─────┬─────┘
                                     │
                               AI analyzes error,
                               fixes script or
                               re-executes fresh
                                     │
                               ┌─────▼─────┐
                               │  Update   │
                               │   Cache   │
                               └───────────┘
```

### Agent Responsibilities

| Agent | Responsibility | When Invoked |
|-------|----------------|--------------|
| **Orchestrator** | Routes tasks, checks cache, manages workflow | Every request |
| **Builder** | Executes via AI while recording actions into RPA script | New/unknown tasks |
| **Executor** | Runs cached RPA scripts (no LLM cost) | Subsequent runs |
| **Recovery** | Handles failures, fixes scripts, updates cache | On RPA errors |
| **Classifier** | Matches user intent to existing RPA scripts | Task routing |

### Task Classification

```
User Input: "like some posts on instagram"
                    │
                    ▼
           ┌─────────────────┐
           │  Task Classifier │
           │   (Embeddings)   │
           └────────┬────────┘
                    │
         ┌──────────┼──────────┐
         │          │          │
         ▼          ▼          ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │Exact    │ │Semantic │ │No       │
    │Match    │ │Match    │ │Match    │
    │         │ │(similar)│ │         │
    └────┬────┘ └────┬────┘ └────┬────┘
         │          │          │
         ▼          ▼          ▼
    Run cached  Ask user to   Builder
    RPA script  confirm or    Agent
                adapt
```

### RPA Script Format

```json
{
  "id": "instagram-like-posts-v1",
  "name": "Like posts on Instagram",
  "created_by": "builder_agent",
  "created_at": "2026-01-15T12:00:00Z",
  "success_count": 47,
  "failure_count": 2,
  "last_updated": "2026-01-15T14:30:00Z",
  "triggers": [
    "like posts on instagram",
    "instagram like",
    "like some ig posts"
  ],
  "steps": [
    {
      "action": "launch_app",
      "package": "com.instagram.android",
      "timeout_ms": 5000
    },
    {
      "action": "wait_for_element",
      "selector": "//android.widget.ImageView[@content-desc='Home']",
      "timeout_ms": 10000
    },
    {
      "action": "tap",
      "selector": "//android.widget.ImageView[@content-desc='Like']",
      "repeat": 3,
      "delay_between_ms": 2000
    }
  ],
  "error_handlers": [
    {
      "error_pattern": "Login required",
      "action": "invoke_recovery_agent",
      "context": "Need to log in first"
    }
  ]
}
```

### User Override Options

Users can control execution mode:

| Mode | Behavior | Use Case |
|------|----------|----------|
| **Auto** (default) | Use cached RPA if available, else AI | Normal operation |
| **Force AI** | Always use AI agent, update cache | UI changed, need fresh approach |
| **Force RPA** | Only use cached script, fail if missing | Predictable execution |
| **Dry Run** | Show what would happen, don't execute | Testing/preview |

### Benefits vs Traditional RPA

| Traditional RPA | AI-Generated RPA |
|-----------------|------------------|
| Manual script creation | Scripts created automatically |
| Breaks when UI changes | Self-healing via Recovery Agent |
| Static, inflexible | Adapts to new scenarios |
| Requires developer | Natural language input |
| Per-platform templates | Learns any app automatically |

---

## Fingerprint System

See [FINGERPRINT-MATRIX.md](./FINGERPRINT-MATRIX.md) for detailed comparison.

### Flow

```
Profile Creation
       │
       ▼
┌─────────────────┐
│  Fingerprint    │
│    Service      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Generate unique │────▶│   devices.json  │
│  identifiers    │     │   (base data)   │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Convert to ENV  │
│   variables     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Docker container│
│ with ENV vars   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│inject-fingerprnt│
│   .sh (boot)    │
└─────────────────┘
```

### Current Parameters (30+)

- Device identity (model, brand, serial, Android ID)
- Build info (fingerprint, SDK, incremental)
- Hardware (board, CPU, bootloader)
- Display (resolution, DPI, refresh rate)
- Graphics (GL renderer, vendor)
- Network (WiFi/BT MAC addresses)
- Locale (timezone, language, region)
- Google Services (GSF ID, GAID)
- Behavioral (boot time / uptime spoofing)

---

## Deployment Architecture

### Self-Hosted (Current)

```
┌─────────────────────────────────────────┐
│              EC2 Instance               │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │   UI    │ │   API   │ │ Worker  │   │
│  │  :3100  │ │  :8100  │ │         │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│  ┌─────────┐ ┌─────────┐               │
│  │Postgres │ │  Redis  │               │
│  │  :5432  │ │  :6379  │               │
│  └─────────┘ └─────────┘               │
│  ┌──────────────────────┐              │
│  │   Redroid Containers │              │
│  │   (per profile)      │              │
│  └──────────────────────┘              │
└─────────────────────────────────────────┘
```

### Future: AWS Marketplace

One-click deployment via AWS Marketplace AMI:
- Pre-configured EC2 AMI with all dependencies
- Kernel modules (binder, ashmem) pre-loaded
- CloudFormation for VPC, security groups
- Optional GPU instances for better performance

---

## Network Architecture (Tailscale Exit Node) - Enterprise

> **Note:** Tailscale integration is an enterprise feature for residential IP routing.

For residential IP routing:

```
┌─────────────────┐     ┌─────────────────┐
│  EC2 Instance   │     │  Home Network   │
│  (MobileDroid)  │     │                 │
│                 │     │  ┌───────────┐  │
│  ┌───────────┐  │     │  │ Tailscale │  │
│  │ Tailscale │──┼─────┼──│ Exit Node │  │
│  │  Client   │  │     │  │ (Raspberry│  │
│  └───────────┘  │     │  │  Pi/NAS)  │  │
│       │         │     │  └───────────┘  │
│       ▼         │     │       │         │
│  Traffic exits  │     │       ▼         │
│  via home IP    │     │  Home Router    │
└─────────────────┘     │  (Residential   │
                        │   IP address)   │
                        └─────────────────┘
```

**Result:** Emulated device shares IP with your real phone.

---

## Future Architecture

### LiteLLM Integration

```
┌─────────────┐
│  AI Agent   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   LiteLLM   │────▶│  Anthropic  │
│   Router    │     │   Claude    │
└──────┬──────┘     └─────────────┘
       │            ┌─────────────┐
       └───────────▶│   OpenAI    │
                    └─────────────┘
                    ┌─────────────┐
                    │   Ollama    │
                    │  (local)    │
                    └─────────────┘
```

### Ollama Self-Hosted LLM

For users who want to avoid API costs:
- Deploy Ollama alongside MobileDroid
- Use smaller models for simple RPA tasks
- Fall back to Claude for complex reasoning

---

*Last updated: January 2026*
