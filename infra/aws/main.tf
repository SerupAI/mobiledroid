terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  default = "us-east-1"
}

variable "instance_type" {
  default = "t3.medium"
}

variable "your_public_ip" {
  description = "Your public IP for SSH/admin access"
  default     = "76.49.30.63/32"
}

variable "tailscale_cidr" {
  description = "Tailscale CGNAT range"
  default     = "100.64.0.0/10"
}

variable "tailscale_ip" {
  description = "Your Tailscale IP"
  default     = "100.110.85.54/32"
}

variable "key_name" {
  description = "EC2 key pair name (leave empty to create new)"
  default     = ""
}

# Get latest Ubuntu 22.04 AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Security Group
resource "aws_security_group" "mobiledroid" {
  name        = "mobiledroid-sg"
  description = "Security group for MobileDroid"

  # SSH - only from your IP and Tailscale
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.your_public_ip, var.tailscale_cidr]
    description = "SSH access"
  }

  # HTTPS - only from your IP and Tailscale
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.your_public_ip, var.tailscale_ip]
    description = "HTTPS"
  }

  # HTTP - only from your IP and Tailscale
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.your_public_ip, var.tailscale_ip]
    description = "HTTP"
  }

  # API port - only from your IP and Tailscale
  ingress {
    from_port   = 8100
    to_port     = 8100
    protocol    = "tcp"
    cidr_blocks = [var.your_public_ip, var.tailscale_cidr]
    description = "API direct access"
  }

  # UI port - only from your IP and Tailscale
  ingress {
    from_port   = 3100
    to_port     = 3100
    protocol    = "tcp"
    cidr_blocks = [var.your_public_ip, var.tailscale_cidr]
    description = "UI direct access"
  }

  # Tailscale UDP
  ingress {
    from_port   = 41641
    to_port     = 41641
    protocol    = "udp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Tailscale"
  }

  # Outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "mobiledroid-sg"
  }
}

# Create key pair if not provided
resource "tls_private_key" "mobiledroid" {
  count     = var.key_name == "" ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 4096
}

resource "aws_key_pair" "mobiledroid" {
  count      = var.key_name == "" ? 1 : 0
  key_name   = "mobiledroid-key"
  public_key = tls_private_key.mobiledroid[0].public_key_openssh
}

resource "local_file" "private_key" {
  count           = var.key_name == "" ? 1 : 0
  content         = tls_private_key.mobiledroid[0].private_key_pem
  filename        = "${path.module}/mobiledroid-key.pem"
  file_permission = "0600"
}

# EC2 Instance
resource "aws_instance" "mobiledroid" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_name != "" ? var.key_name : aws_key_pair.mobiledroid[0].key_name

  vpc_security_group_ids = [aws_security_group.mobiledroid.id]

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
  }

  user_data = file("${path.module}/user-data.sh")

  tags = {
    Name = "mobiledroid"
  }
}

# Elastic IP for stable address
resource "aws_eip" "mobiledroid" {
  instance = aws_instance.mobiledroid.id
  domain   = "vpc"

  tags = {
    Name = "mobiledroid-eip"
  }
}

# Outputs
output "public_ip" {
  value = aws_eip.mobiledroid.public_ip
}

output "ssh_command" {
  value = var.key_name == "" ? "ssh -i ${path.module}/mobiledroid-key.pem ubuntu@${aws_eip.mobiledroid.public_ip}" : "ssh ubuntu@${aws_eip.mobiledroid.public_ip}"
}

output "ui_url" {
  value = "http://${aws_eip.mobiledroid.public_ip}:3100"
}

output "api_url" {
  value = "http://${aws_eip.mobiledroid.public_ip}:8100"
}
