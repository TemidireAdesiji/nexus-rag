terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket         = "nexus-rag-terraform-state"
    key            = "aws/eks/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "nexus-rag-tf-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "nexus-rag"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}

provider "kubernetes" {
  host                   = aws_eks_cluster.nexus.endpoint
  cluster_ca_certificate = base64decode(aws_eks_cluster.nexus.certificate_authority[0].data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", var.cluster_name]
  }
}
