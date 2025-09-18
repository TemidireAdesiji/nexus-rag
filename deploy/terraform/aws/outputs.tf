output "cluster_endpoint" {
  description = "EKS cluster API server endpoint"
  value       = aws_eks_cluster.nexus.endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = aws_eks_cluster.nexus.name
}

output "cluster_ca_cert" {
  description = "Base64-encoded CA certificate for the cluster"
  value       = aws_eks_cluster.nexus.certificate_authority[0].data
  sensitive   = true
}

output "kubeconfig_command" {
  description = "Command to update kubeconfig for cluster access"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${aws_eks_cluster.nexus.name}"
}

output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.nexus.id
}

output "ecr_gateway_url" {
  description = "ECR repository URL for gateway image"
  value       = aws_ecr_repository.gateway.repository_url
}

output "ecr_data_api_url" {
  description = "ECR repository URL for data-api image"
  value       = aws_ecr_repository.data_api.repository_url
}

output "ecr_ui_url" {
  description = "ECR repository URL for ui image"
  value       = aws_ecr_repository.ui.repository_url
}
