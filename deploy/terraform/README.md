# MobileDroid Terraform Deployment

Deploy MobileDroid to AWS EC2 using Terraform.

## Prerequisites

- [Terraform](https://terraform.io/downloads) >= 1.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- AWS account with EC2 permissions

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/serup-ai/mobiledroid.git
cd mobiledroid/deploy/terraform

# 2. Configure variables
cp terraform.tfvars.example terraform.tfvars
nano terraform.tfvars  # Edit with your settings

# 3. Initialize Terraform
terraform init

# 4. Review the plan
terraform plan

# 5. Deploy
terraform apply
```

## Configuration

Edit `terraform.tfvars` before deploying:

### Required Settings

```hcl
# Restrict SSH to your IP (IMPORTANT for security)
# Find your IP: curl -s https://api.ipify.org
allowed_ssh_cidrs = ["YOUR.PUBLIC.IP/32"]
```

### Optional Settings

```hcl
# AWS region
aws_region = "us-east-1"

# Instance type (t3.xlarge recommended)
instance_type = "t3.xlarge"

# Anthropic API key for AI agent
anthropic_api_key = "sk-ant-..."
```

## Instance Types

| Type | vCPU | RAM | Cost/mo | Notes |
|------|------|-----|---------|-------|
| t3.medium | 2 | 4GB | ~$30 | Minimum viable |
| t3.large | 2 | 8GB | ~$60 | Recommended dev |
| t3.xlarge | 4 | 16GB | ~$120 | Recommended prod |

## Outputs

After deployment, Terraform will output:

```
public_ip   = "x.x.x.x"
ui_url      = "http://x.x.x.x:3100"
api_url     = "http://x.x.x.x:8100"
ssh_command = "ssh -i mobiledroid-key.pem ubuntu@x.x.x.x"
```

## Post-Deployment

### Set API Key (if not set during deploy)

```bash
# SSH into instance
ssh -i mobiledroid-key.pem ubuntu@<public_ip>

# Edit .env file
nano /opt/mobiledroid/app/.env

# Add your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# Restart services
/opt/mobiledroid/restart.sh
```

### Helper Scripts

The instance includes helper scripts in `/opt/mobiledroid/`:

```bash
./status.sh   # Check system status
./logs.sh     # View container logs
./restart.sh  # Restart all services
./update.sh   # Pull latest code and restart
```

## Destroy

To tear down the infrastructure:

```bash
terraform destroy
```

## Security Recommendations

1. **Restrict SSH access** - Set `allowed_ssh_cidrs` to your IP only
2. **Use Elastic IP** - Keeps address stable across restarts
3. **Enable HTTPS** - Set up a reverse proxy with SSL
4. **Backup data** - The SQLite database is in `/opt/mobiledroid/app/data`

## Troubleshooting

### Containers not starting

Check kernel modules:
```bash
lsmod | grep binder
```

If missing, reboot the instance:
```bash
sudo reboot
```

### View logs

```bash
cd /opt/mobiledroid/app/docker
docker compose logs -f
```

### Check user-data script

```bash
cat /var/log/user-data.log
```
