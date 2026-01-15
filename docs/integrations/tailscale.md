# Tailscale Exit Node Integration

Route your MobileDroid container traffic through your home network using Tailscale exit nodes. This provides a residential IP address for better evasion.

## Overview

```
┌───────────────────┐     ┌──────────────────┐     ┌────────────────┐
│  MobileDroid      │     │   Tailscale      │     │  Home Device   │
│  (EC2/Cloud)      │────▶│   Network        │────▶│  (Exit Node)   │
│                   │     │                  │     │                │
│  Container ───────│─────│───────────────────│─────│───▶ Internet  │
└───────────────────┘     └──────────────────┘     └────────────────┘
                                                         Your Home IP
```

Traffic from MobileDroid containers routes through your home network, appearing to originate from your residential IP address.

## Prerequisites

- A Tailscale account (free tier works)
- A device at home that can run 24/7 (Raspberry Pi, old laptop, etc.)
- MobileDroid server (EC2 or other cloud instance)

## Setup Instructions

### Step 1: Set Up Home Exit Node

On your home device (Raspberry Pi, Linux server, etc.):

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Connect and advertise as exit node
sudo tailscale up --advertise-exit-node
```

Then approve the exit node in Tailscale admin:

1. Go to [admin.tailscale.com](https://admin.tailscale.com)
2. Find your home device in the Machines list
3. Click the three dots menu
4. Enable "Exit Node"

### Step 2: Set Up MobileDroid Server

On your EC2/cloud server running MobileDroid:

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Connect to your tailnet
sudo tailscale up

# (Optional) Start SOCKS5 proxy server
# This allows containers to route through Tailscale
sudo tailscale up --socks5-server=0.0.0.0:1055
```

### Step 3: Configure MobileDroid

Using the API:

```bash
# Configure Tailscale connector with your home device name
curl -X POST http://localhost:8100/connectors/tailscale/configure \
  -H "Content-Type: application/json" \
  -d '{"exit_node": "your-home-device-name"}'

# Enable the connector
curl -X POST http://localhost:8100/connectors/tailscale/enable

# Connect to exit node
curl -X POST http://localhost:8100/connectors/tailscale/connect
```

### Step 4: Create Profile with Tailscale

```bash
# Create a profile using Tailscale for proxy
curl -X POST http://localhost:8100/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Residential Profile",
    "fingerprint": {
      "model": "Pixel 8",
      "brand": "google",
      "manufacturer": "Google",
      "build_fingerprint": "google/shiba/shiba:14/UD1A.231105.004/11010374:user/release-keys"
    },
    "proxy_connector_id": "tailscale"
  }'
```

## Verifying It Works

### Check Tailscale Status

```bash
curl http://localhost:8100/connectors/tailscale/status
```

Response:
```json
{
  "connected": true,
  "healthy": true,
  "message": "Connected via exit node",
  "details": {
    "backend_state": "Running",
    "exit_node": "your-home-device",
    "tailscale_ip": "100.x.x.x",
    "configured_exit_node": "your-home-device"
  }
}
```

### Check Public IP

```bash
curl http://localhost:8100/connectors/tailscale/ip
```

Response:
```json
{
  "ip": "203.0.113.45",  // Should be your home IP
  "exit_node_active": true
}
```

### List Available Exit Nodes

```bash
curl http://localhost:8100/connectors/tailscale/nodes
```

Response:
```json
{
  "nodes": [
    {
      "id": "nodeABC123",
      "hostname": "home-pi",
      "dns_name": "home-pi.your-tailnet.ts.net",
      "ips": ["100.64.0.5"],
      "online": true,
      "active": true
    }
  ]
}
```

## API Reference

### Connector Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/connectors` | GET | List all connectors |
| `/connectors/tailscale` | GET | Get Tailscale connector details |
| `/connectors/tailscale/status` | GET | Check Tailscale status |
| `/connectors/tailscale/configure` | POST | Configure exit node |
| `/connectors/tailscale/enable` | POST | Enable connector |
| `/connectors/tailscale/disable` | POST | Disable connector |
| `/connectors/tailscale/connect` | POST | Connect to exit node |
| `/connectors/tailscale/disconnect` | POST | Disconnect from exit node |
| `/connectors/tailscale/nodes` | GET | List available exit nodes |
| `/connectors/tailscale/ip` | GET | Check current public IP |

### Configuration Options

```json
{
  "exit_node": "hostname",    // Required: Exit node hostname
  "tailnet": "example.org"    // Optional: Tailnet domain
}
```

## Troubleshooting

### "Tailscale is not installed"

Install Tailscale on the server:
```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

### "No exit nodes available"

1. Check your home device is online: `tailscale status`
2. Verify exit node is approved in Tailscale admin
3. Ensure home device is running: `sudo tailscale up --advertise-exit-node`

### Container traffic not routing through exit node

1. Verify Tailscale SOCKS5 proxy is running: `tailscale status`
2. Check container can reach host network
3. Ensure profile has `proxy_connector_id: "tailscale"`

### Slow connection

- Exit node bandwidth is limited by your home internet
- Consider upgrading home internet or using closer exit node

## Security Notes

- Your home IP will be exposed to target websites
- All traffic from profiles using Tailscale will route through your home
- Consider using separate Tailscale account for MobileDroid if needed
- Exit node sees all traffic - ensure you trust the device

## Alternative: Manual Proxy Configuration

If you prefer not to use the Tailscale connector, you can manually configure SOCKS5 proxy:

```bash
# Start Tailscale SOCKS5 proxy on server
sudo tailscale up --socks5-server=localhost:1055 --exit-node=home-device

# Create profile with manual proxy config
curl -X POST http://localhost:8100/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Manual SOCKS Profile",
    "fingerprint": { ... },
    "proxy": {
      "type": "socks5",
      "host": "host.docker.internal",
      "port": 1055
    }
  }'
```
