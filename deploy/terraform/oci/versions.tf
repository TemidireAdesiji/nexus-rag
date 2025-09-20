terraform {
  required_version = ">= 1.5.0"

  required_providers {
    oci = {
      source  = "oracle/oci"
      version = "~> 5.30"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
  }

  backend "s3" {
    bucket   = "nexus-rag-terraform-state"
    key      = "oci/oke/terraform.tfstate"
    region   = "us-ashburn-1"
    endpoint = "https://<namespace>.compat.objectstorage.us-ashburn-1.oraclecloud.com"

    skip_region_validation      = true
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
  }
}

provider "oci" {
  region = var.oci_region
}

provider "kubernetes" {
  host                   = oci_containerengine_cluster.nexus.endpoints[0].kubernetes
  cluster_ca_certificate = base64decode(oci_containerengine_cluster.nexus.endpoints[0].public_endpoint != "" ? oci_containerengine_cluster.nexus.metadata[0].cluster_ca_cert : "")

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "oci"
    args        = ["ce", "cluster", "generate-token", "--cluster-id", oci_containerengine_cluster.nexus.id]
  }
}
