# Technical Specification: n8n Integration Node

## Overview

Build a community node for [n8n](https://n8n.io) that enables workflow automation with MobileDroid. n8n is an open-source workflow automation tool with 400+ integrations.

**Goals:**
- Support both self-hosted MobileDroid and MobileDroid Cloud
- Expose all major MobileDroid capabilities as n8n actions
- Enable event-driven triggers from MobileDroid
- Publish to n8n community nodes registry

---

## Architecture

### Deployment Options

```
┌─────────────────────────────────────────────────────────────────┐
│                         n8n Workflow                             │
│  ┌─────────┐    ┌─────────────────┐    ┌─────────┐             │
│  │ Trigger │───▶│ MobileDroid Node│───▶│ Action  │             │
│  │ (Slack) │    │                 │    │ (Email) │             │
│  └─────────┘    └────────┬────────┘    └─────────┘             │
└──────────────────────────┼──────────────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           │                               │
           ▼                               ▼
┌─────────────────────┐       ┌─────────────────────┐
│   Self-Hosted       │       │   MobileDroid Cloud │
│   MobileDroid       │       │   (api.mobiledroid  │
│   (user's server)   │       │    .cloud)          │
│                     │       │                     │
│ http://192.168.x:   │       │ https://api.mobile  │
│ 8100                │       │ droid.cloud         │
└─────────────────────┘       └─────────────────────┘
```

### Authentication

| Mode | Auth Method | Configuration |
|------|-------------|---------------|
| **Self-hosted** | API Key (optional) or none | User provides base URL |
| **Cloud** | API Key (required) | Pre-configured URL, user provides API key |

```typescript
// Credential types
interface MobileDroidCredentials {
  mode: 'self-hosted' | 'cloud';
  baseUrl?: string;      // Required for self-hosted
  apiKey?: string;       // Required for cloud, optional for self-hosted
}
```

---

## Node Structure

### Package Info

```
n8n-nodes-mobiledroid/
├── nodes/
│   └── MobileDroid/
│       ├── MobileDroid.node.ts      # Main node definition
│       ├── MobileDroidTrigger.node.ts # Webhook trigger node
│       └── GenericFunctions.ts      # API helper functions
├── credentials/
│   └── MobileDroidApi.credentials.ts
└── package.json
```

---

## Actions (Operations)

### Profile Management

| Action | Description | Parameters |
|--------|-------------|------------|
| `profile.list` | List all profiles | `limit`, `offset` |
| `profile.get` | Get profile details | `profileId` |
| `profile.create` | Create new profile | `name`, `fingerprintId`, `proxy` |
| `profile.delete` | Delete profile | `profileId` |
| `profile.start` | Start profile | `profileId`, `waitForReady` |
| `profile.stop` | Stop profile | `profileId` |
| `profile.screenshot` | Take screenshot | `profileId`, `format` |

### AI Agent

| Action | Description | Parameters |
|--------|-------------|------------|
| `agent.chat` | Send AI command | `profileId`, `message`, `maxSteps`, `requireApproval` |
| `agent.chatStream` | Stream AI response | `profileId`, `message`, `maxSteps` |
| `automation.run` | Run learned automation | `profileId`, `automationId` |

### App Management

| Action | Description | Parameters |
|--------|-------------|------------|
| `app.install` | Install app | `profileId`, `appId`, `waitForInstall` |
| `app.launch` | Launch app | `profileId`, `packageName` |
| `app.list` | List installed apps | `profileId` |
| `app.uninstall` | Uninstall app | `profileId`, `packageName` |

### Device Control (Low-Level)

| Action | Description | Parameters |
|--------|-------------|------------|
| `device.tap` | Tap coordinates | `profileId`, `x`, `y` |
| `device.type` | Type text | `profileId`, `text` |
| `device.swipe` | Swipe gesture | `profileId`, `startX`, `startY`, `endX`, `endY` |
| `device.key` | Press key | `profileId`, `keyCode` |
| `device.shell` | Run ADB shell | `profileId`, `command` |

### Proxy Management

| Action | Description | Parameters |
|--------|-------------|------------|
| `proxy.set` | Set profile proxy | `profileId`, `connectorId`, `country` |
| `proxy.clear` | Clear proxy | `profileId` |
| `proxy.rotate` | Rotate proxy | `profileId` |

### Snapshots

| Action | Description | Parameters |
|--------|-------------|------------|
| `snapshot.create` | Create snapshot | `profileId`, `name` |
| `snapshot.restore` | Restore snapshot | `profileId`, `snapshotId` |
| `snapshot.list` | List snapshots | `profileId` |

---

## Triggers (Webhooks)

MobileDroid would need webhook support to enable triggers.

| Trigger | Fires When | Payload |
|---------|------------|---------|
| `task.completed` | AI task finishes | `profileId`, `taskId`, `success`, `result` |
| `profile.statusChanged` | Profile starts/stops | `profileId`, `oldStatus`, `newStatus` |
| `automation.failed` | Learned automation fails | `profileId`, `automationId`, `error` |
| `screenshot.ready` | Screenshot captured | `profileId`, `imageUrl` |

### Webhook Implementation Required

```python
# New API endpoint needed in MobileDroid
POST /webhooks
{
  "url": "https://user-n8n.example.com/webhook/xxx",
  "events": ["task.completed", "profile.statusChanged"],
  "secret": "webhook-signing-secret"
}
```

---

## Example Workflows

### 1. Scheduled Social Media Posting

```
Schedule Trigger (daily 9am)
    │
    ▼
MobileDroid: Start Profile
    │
    ▼
MobileDroid: AI Chat "Open Instagram and post the image from /sdcard/post.jpg with caption 'Good morning!'"
    │
    ▼
MobileDroid: Stop Profile
    │
    ▼
Slack: Send notification "Posted to Instagram"
```

### 2. Multi-Account Data Collection

```
Webhook Trigger (new product URL)
    │
    ▼
Loop: For each profile
    │
    ├──▶ MobileDroid: Start Profile
    │
    ├──▶ MobileDroid: AI Chat "Open Amazon and search for {product}, get price"
    │
    ├──▶ MobileDroid: Screenshot
    │
    └──▶ MobileDroid: Stop Profile
    │
    ▼
Google Sheets: Append price data
```

### 3. Auto-Healing Automation

```
Schedule Trigger (hourly)
    │
    ▼
MobileDroid: Run Learned Automation "check-notifications"
    │
    ├── Success ──▶ Slack: "Notifications checked"
    │
    └── Failure ──▶ MobileDroid: AI Chat "Fix and update the notification checking automation"
                        │
                        ▼
                    Slack: "Automation self-healed"
```

---

## Implementation Phases

### Phase 1: Core Node (MVP)
- [ ] Credential configuration (self-hosted + cloud)
- [ ] Profile actions (list, create, start, stop, screenshot)
- [ ] AI chat action (non-streaming)
- [ ] Publish to npm as community node

### Phase 2: Full Actions
- [ ] App management actions
- [ ] Device control actions
- [ ] Proxy management actions
- [ ] Snapshot actions
- [ ] Streaming AI chat (if n8n supports)

### Phase 3: Triggers
- [ ] Add webhook support to MobileDroid API
- [ ] Implement trigger node
- [ ] Event subscriptions

### Phase 4: Advanced
- [ ] Learned automation actions
- [ ] Multi-profile batch operations
- [ ] Binary data handling (screenshots, files)

---

## Technical Requirements

### n8n Node Development

```bash
# n8n community node template
npx n8n-node-dev init

# Structure
n8n-nodes-mobiledroid/
├── package.json
├── tsconfig.json
├── nodes/
│   └── MobileDroid/
│       ├── MobileDroid.node.ts
│       ├── MobileDroid.node.json    # Node metadata
│       └── mobiledroid.svg          # Icon
├── credentials/
│   └── MobileDroidApi.credentials.ts
└── index.ts
```

### Dependencies

```json
{
  "name": "n8n-nodes-mobiledroid",
  "version": "0.1.0",
  "description": "n8n nodes for MobileDroid Android automation",
  "keywords": ["n8n", "n8n-community-node", "mobiledroid", "android", "automation"],
  "n8n": {
    "n8nNodesApiVersion": 1,
    "credentials": ["MobileDroidApi"],
    "nodes": ["MobileDroid", "MobileDroidTrigger"]
  }
}
```

### API Client

```typescript
// GenericFunctions.ts
import { IExecuteFunctions, IHttpRequestOptions } from 'n8n-workflow';

export async function mobileDroidApiRequest(
  this: IExecuteFunctions,
  method: string,
  endpoint: string,
  body?: object,
): Promise<any> {
  const credentials = await this.getCredentials('mobileDroidApi');

  const baseUrl = credentials.mode === 'cloud'
    ? 'https://api.mobiledroid.cloud'
    : credentials.baseUrl;

  const options: IHttpRequestOptions = {
    method,
    url: `${baseUrl}${endpoint}`,
    body,
    headers: credentials.apiKey ? {
      'Authorization': `Bearer ${credentials.apiKey}`
    } : {},
  };

  return this.helpers.httpRequest(options);
}
```

---

## MobileDroid API Changes Required

### For Triggers (Phase 3)

New webhook management endpoints:

```
POST   /webhooks              # Create webhook subscription
GET    /webhooks              # List subscriptions
DELETE /webhooks/{id}         # Delete subscription
POST   /webhooks/{id}/test    # Test webhook
```

Webhook payload signing:

```python
import hmac
import hashlib

def sign_webhook(payload: dict, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        json.dumps(payload).encode(),
        hashlib.sha256
    ).hexdigest()
```

### For Cloud (Authentication)

API key authentication middleware (if not already present):

```python
# Bearer token auth for cloud
async def verify_api_key(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(401)
    api_key = authorization[7:]
    # Validate against database
```

---

## Publishing

### npm Registry

```bash
npm login
npm publish --access public
```

### n8n Community Nodes

1. Submit to [n8n community nodes list](https://github.com/n8n-io/n8n/blob/master/packages/nodes-base/nodes.json)
2. Create demo workflow templates
3. Write documentation

---

## Files to Create

| File | Location | Description |
|------|----------|-------------|
| `package.json` | `packages/n8n-node/` | Node package config |
| `MobileDroid.node.ts` | `packages/n8n-node/nodes/` | Main node |
| `MobileDroidTrigger.node.ts` | `packages/n8n-node/nodes/` | Trigger node |
| `MobileDroidApi.credentials.ts` | `packages/n8n-node/credentials/` | Auth config |
| `GenericFunctions.ts` | `packages/n8n-node/nodes/` | API helpers |

---

## Verification

- [ ] Node installs in n8n via npm
- [ ] Self-hosted connection works
- [ ] Cloud connection works with API key
- [ ] All profile actions function correctly
- [ ] AI chat returns results
- [ ] Screenshots download as binary
- [ ] Triggers fire on events (Phase 3)
