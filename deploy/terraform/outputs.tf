# MobileDroid Terraform Outputs

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.mobiledroid.id
}

output "public_ip" {
  description = "Public IP address"
  value       = var.create_elastic_ip ? aws_eip.mobiledroid[0].public_ip : aws_instance.mobiledroid.public_ip
}

output "private_ip" {
  description = "Private IP address"
  value       = aws_instance.mobiledroid.private_ip
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = var.key_name == "" ? "ssh -i ${var.project_name}-key.pem ubuntu@${var.create_elastic_ip ? aws_eip.mobiledroid[0].public_ip : aws_instance.mobiledroid.public_ip}" : "ssh ubuntu@${var.create_elastic_ip ? aws_eip.mobiledroid[0].public_ip : aws_instance.mobiledroid.public_ip}"
}

output "ui_url" {
  description = "MobileDroid UI URL"
  value       = "http://${var.create_elastic_ip ? aws_eip.mobiledroid[0].public_ip : aws_instance.mobiledroid.public_ip}:3100"
}

output "api_url" {
  description = "MobileDroid API URL"
  value       = "http://${var.create_elastic_ip ? aws_eip.mobiledroid[0].public_ip : aws_instance.mobiledroid.public_ip}:8100"
}

output "api_docs_url" {
  description = "MobileDroid API documentation"
  value       = "http://${var.create_elastic_ip ? aws_eip.mobiledroid[0].public_ip : aws_instance.mobiledroid.public_ip}:8100/docs"
}
