# MobileDroid AWS EC2 Terraform Configuration
#
# This creates an EC2 instance with MobileDroid pre-installed.
# Customize variables in terraform.tfvars before running.

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
  name        = "${var.project_name}-sg"
  description = "Security group for MobileDroid"

  # SSH - restricted to allowed IPs
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_ssh_cidrs
    description = "SSH access"
  }

  # Web UI
  ingress {
    from_port   = 3100
    to_port     = 3100
    protocol    = "tcp"
    cidr_blocks = var.allowed_web_cidrs
    description = "MobileDroid UI"
  }

  # API
  ingress {
    from_port   = 8100
    to_port     = 8100
    protocol    = "tcp"
    cidr_blocks = var.allowed_web_cidrs
    description = "MobileDroid API"
  }

  # HTTP (optional, for reverse proxy)
  dynamic "ingress" {
    for_each = var.enable_http ? [1] : []
    content {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      cidr_blocks = var.allowed_web_cidrs
      description = "HTTP"
    }
  }

  # HTTPS (optional, for reverse proxy)
  dynamic "ingress" {
    for_each = var.enable_https ? [1] : []
    content {
      from_port   = 443
      to_port     = 443
      protocol    = "tcp"
      cidr_blocks = var.allowed_web_cidrs
      description = "HTTPS"
    }
  }

  # Outbound - allow all
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name    = "${var.project_name}-sg"
    Project = var.project_name
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
  key_name   = "${var.project_name}-key"
  public_key = tls_private_key.mobiledroid[0].public_key_openssh

  tags = {
    Name    = "${var.project_name}-key"
    Project = var.project_name
  }
}

resource "local_file" "private_key" {
  count           = var.key_name == "" ? 1 : 0
  content         = tls_private_key.mobiledroid[0].private_key_pem
  filename        = "${path.module}/${var.project_name}-key.pem"
  file_permission = "0600"
}

# EC2 Instance
resource "aws_instance" "mobiledroid" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = var.instance_type
  key_name      = var.key_name != "" ? var.key_name : aws_key_pair.mobiledroid[0].key_name

  vpc_security_group_ids = [aws_security_group.mobiledroid.id]

  root_block_device {
    volume_size = var.volume_size
    volume_type = "gp3"
  }

  user_data = templatefile("${path.module}/user-data.sh", {
    anthropic_api_key = var.anthropic_api_key
    openai_api_key    = var.openai_api_key
  })

  tags = {
    Name    = var.project_name
    Project = var.project_name
  }
}

# Elastic IP (optional)
resource "aws_eip" "mobiledroid" {
  count    = var.create_elastic_ip ? 1 : 0
  instance = aws_instance.mobiledroid.id
  domain   = "vpc"

  tags = {
    Name    = "${var.project_name}-eip"
    Project = var.project_name
  }
}
