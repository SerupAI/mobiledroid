# MobileDroid Kubernetes Deployment

Deploy MobileDroid to Kubernetes.

## Important Requirements

MobileDroid uses Redroid (Android in Docker) which requires:

1. **Docker on nodes** - Kubernetes nodes must have Docker installed (not just containerd)
2. **Docker socket access** - The API pod mounts `/var/run/docker.sock`
3. **Kernel modules** - Nodes must have `binder_linux` and `ashmem_linux` modules loaded
4. **Privileged pods** - Redroid containers require privileged mode

### Node Preparation

Before deploying, prepare your Kubernetes nodes:

```bash
# On each node, load required kernel modules
sudo modprobe binder_linux devices="binder,hwbinder,vndbinder"
sudo modprobe ashmem_linux

# Make persistent across reboots
echo "binder_linux" | sudo tee -a /etc/modules-load.d/redroid.conf
echo "ashmem_linux" | sudo tee -a /etc/modules-load.d/redroid.conf
echo 'options binder_linux devices="binder,hwbinder,vndbinder"' | sudo tee /etc/modprobe.d/redroid.conf
```

## Quick Start

```bash
# 1. Create secrets
cp secret.yaml.example secret.yaml
# Edit secret.yaml with your base64-encoded API keys
# echo -n "sk-ant-xxx" | base64

# 2. Uncomment secret.yaml in kustomization.yaml
nano kustomization.yaml

# 3. Deploy
kubectl apply -k .

# 4. Check status
kubectl get pods -n mobiledroid

# 5. Port forward for local access
kubectl port-forward -n mobiledroid svc/ui 3100:3000 &
kubectl port-forward -n mobiledroid svc/api 8100:8000 &
```

## Components

| Component | Description | Port |
|-----------|-------------|------|
| `api` | FastAPI backend | 8000 |
| `ui` | Next.js frontend | 3000 |
| `postgres` | PostgreSQL database | 5432 |
| `redis` | Redis cache | 6379 |

## Configuration

### Secrets

Create `secret.yaml` from the example and add your API keys:

```bash
# Encode your API key
echo -n "sk-ant-api03-xxx" | base64
# Output: c2stYW50LWFwaTAzLXh4eA==

# Add to secret.yaml
ANTHROPIC_API_KEY: c2stYW50LWFwaTAzLXh4eA==
```

### Ingress

To expose externally with a domain:

1. Install an Ingress Controller (nginx-ingress, traefik)
2. Edit `ingress.yaml` with your domain
3. Uncomment `ingress.yaml` in `kustomization.yaml`
4. Apply: `kubectl apply -k .`

## Scaling

The API and UI can be scaled horizontally:

```bash
kubectl scale deployment api -n mobiledroid --replicas=3
kubectl scale deployment ui -n mobiledroid --replicas=3
```

Note: Each API replica needs access to Docker socket on its node.

## Storage

- **PostgreSQL**: Uses PersistentVolumeClaim (10Gi default)
- **API data**: Uses emptyDir (consider PVC for production)

## Monitoring

```bash
# View logs
kubectl logs -n mobiledroid -l app=api -f
kubectl logs -n mobiledroid -l app=ui -f

# Check pod status
kubectl get pods -n mobiledroid -w

# Describe for troubleshooting
kubectl describe pod -n mobiledroid -l app=api
```

## Troubleshooting

### Pods not starting

Check kernel modules on the node:
```bash
kubectl get pods -n mobiledroid -o wide  # Find node
ssh <node> "lsmod | grep binder"
```

### API can't connect to Docker

Verify Docker socket is mounted:
```bash
kubectl exec -n mobiledroid deploy/api -- ls -la /var/run/docker.sock
```

### Database connection issues

Check PostgreSQL is running:
```bash
kubectl logs -n mobiledroid -l app=postgres
kubectl exec -n mobiledroid deploy/postgres -- pg_isready
```

## Cleanup

```bash
kubectl delete -k .
```

## Alternative: Single-Node Deployment

For simpler deployments, consider using Docker Compose on a single VM instead:

- [AWS CloudFormation](../aws/) - One-click EC2 deployment
- [Terraform](../terraform/) - Infrastructure as code
- [DigitalOcean/Vultr](../README.md) - VPS with install scripts
