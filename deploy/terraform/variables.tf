# MobileDroid Terraform Variables
#
# Copy terraform.tfvars.example to terraform.tfvars and customize.

variable "project_name" {
  description = "Name prefix for all resources"
  type        = string
  default     = "mobiledroid"
}

variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type (t3.medium minimum, t3.xlarge recommended)"
  type        = string
  default     = "t3.xlarge"
}

variable "volume_size" {
  description = "Root volume size in GB"
  type        = number
  default     = 30
}

variable "key_name" {
  description = "Existing EC2 key pair name (leave empty to create new)"
  type        = string
  default     = ""
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to SSH (recommend restricting to your IP)"
  type        = list(string)
  default     = ["0.0.0.0/0"] # CHANGE THIS to your IP: ["YOUR.IP.HERE/32"]
}

variable "allowed_web_cidrs" {
  description = "CIDR blocks allowed to access web UI/API"
  type        = list(string)
  default     = ["0.0.0.0/0"] # CHANGE THIS for production
}

variable "enable_http" {
  description = "Enable HTTP port 80 (for reverse proxy)"
  type        = bool
  default     = false
}

variable "enable_https" {
  description = "Enable HTTPS port 443 (for reverse proxy)"
  type        = bool
  default     = false
}

variable "create_elastic_ip" {
  description = "Create an Elastic IP for stable public address"
  type        = bool
  default     = true
}

# API Keys (optional - can also be set after deployment)
variable "anthropic_api_key" {
  description = "Anthropic API key for AI agent (optional, can set later)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API key (optional)"
  type        = string
  default     = ""
  sensitive   = true
}
