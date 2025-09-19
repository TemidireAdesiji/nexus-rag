variable "oci_region" {
  description = "OCI region for the OKE cluster"
  type        = string
  default     = "us-ashburn-1"
}

variable "compartment_id" {
  description = "OCI compartment OCID for all resources"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, production)"
  type        = string
  default     = "production"
}

variable "cluster_name" {
  description = "Name of the OKE cluster"
  type        = string
  default     = "nexus-rag-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version for the OKE cluster"
  type        = string
  default     = "v1.29.1"
}

variable "vcn_cidr" {
  description = "CIDR block for the VCN"
  type        = string
  default     = "10.20.0.0/16"
}

variable "node_shape" {
  description = "Compute shape for worker nodes"
  type        = string
  default     = "VM.Standard.E4.Flex"
}

variable "node_ocpus" {
  description = "Number of OCPUs per worker node (flex shape)"
  type        = number
  default     = 2
}

variable "node_memory_gb" {
  description = "Memory in GB per worker node (flex shape)"
  type        = number
  default     = 16
}

variable "node_pool_size" {
  description = "Number of worker nodes in the node pool"
  type        = number
  default     = 3
}

variable "node_image_id" {
  description = "OCID of the Oracle Linux image for worker nodes"
  type        = string
  default     = ""
}

variable "ssh_public_key" {
  description = "SSH public key for worker node access"
  type        = string
  default     = ""
}
