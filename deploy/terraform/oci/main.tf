data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

locals {
  ad_names = data.oci_identity_availability_domains.ads.availability_domains[*].name
}

# ──────────────────────────────────────────────
# VCN
# ──────────────────────────────────────────────

resource "oci_core_vcn" "nexus" {
  compartment_id = var.compartment_id
  display_name   = "${var.cluster_name}-vcn"
  cidr_blocks    = [var.vcn_cidr]
  dns_label      = "nexusrag"

  freeform_tags = {
    Project     = "nexus-rag"
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}

resource "oci_core_internet_gateway" "nexus" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.nexus.id
  display_name   = "${var.cluster_name}-igw"
  enabled        = true
}

resource "oci_core_nat_gateway" "nexus" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.nexus.id
  display_name   = "${var.cluster_name}-nat"
}

resource "oci_core_route_table" "public" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.nexus.id
  display_name   = "${var.cluster_name}-public-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_internet_gateway.nexus.id
  }
}

resource "oci_core_route_table" "private" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.nexus.id
  display_name   = "${var.cluster_name}-private-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    network_entity_id = oci_core_nat_gateway.nexus.id
  }
}

resource "oci_core_security_list" "k8s_api" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.nexus.id
  display_name   = "${var.cluster_name}-k8s-api-sl"

  ingress_security_rules {
    protocol  = "6"
    source    = "0.0.0.0/0"
    stateless = false
    tcp_options {
      min = 6443
      max = 6443
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }
}

resource "oci_core_security_list" "worker_nodes" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.nexus.id
  display_name   = "${var.cluster_name}-worker-sl"

  ingress_security_rules {
    protocol  = "all"
    source    = var.vcn_cidr
    stateless = false
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }
}

resource "oci_core_subnet" "k8s_endpoint" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.nexus.id
  display_name               = "${var.cluster_name}-k8s-endpoint"
  cidr_block                 = cidrsubnet(var.vcn_cidr, 8, 0)
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.k8s_api.id]
  prohibit_public_ip_on_vnic = false
  dns_label                  = "k8sendpoint"
}

resource "oci_core_subnet" "node_pool" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.nexus.id
  display_name               = "${var.cluster_name}-node-pool"
  cidr_block                 = cidrsubnet(var.vcn_cidr, 8, 10)
  route_table_id             = oci_core_route_table.private.id
  security_list_ids          = [oci_core_security_list.worker_nodes.id]
  prohibit_public_ip_on_vnic = true
  dns_label                  = "nodepool"
}

resource "oci_core_subnet" "service_lb" {
  compartment_id             = var.compartment_id
  vcn_id                     = oci_core_vcn.nexus.id
  display_name               = "${var.cluster_name}-service-lb"
  cidr_block                 = cidrsubnet(var.vcn_cidr, 8, 20)
  route_table_id             = oci_core_route_table.public.id
  security_list_ids          = [oci_core_security_list.k8s_api.id]
  prohibit_public_ip_on_vnic = false
  dns_label                  = "servicelb"
}

# ──────────────────────────────────────────────
# OKE Cluster
# ──────────────────────────────────────────────

resource "oci_containerengine_cluster" "nexus" {
  compartment_id     = var.compartment_id
  kubernetes_version = var.kubernetes_version
  name               = var.cluster_name
  vcn_id             = oci_core_vcn.nexus.id

  endpoint_config {
    is_public_ip_enabled = true
    subnet_id            = oci_core_subnet.k8s_endpoint.id
  }

  options {
    service_lb_subnet_ids = [oci_core_subnet.service_lb.id]

    kubernetes_network_config {
      pods_cidr     = "10.244.0.0/16"
      services_cidr = "10.96.0.0/16"
    }
  }

  freeform_tags = {
    Project     = "nexus-rag"
    ManagedBy   = "terraform"
    Environment = var.environment
  }
}

# ──────────────────────────────────────────────
# Node Pool
# ──────────────────────────────────────────────

resource "oci_containerengine_node_pool" "nexus" {
  compartment_id     = var.compartment_id
  cluster_id         = oci_containerengine_cluster.nexus.id
  kubernetes_version = var.kubernetes_version
  name               = "${var.cluster_name}-pool"

  node_shape = var.node_shape

  node_shape_config {
    ocpus         = var.node_ocpus
    memory_in_gbs = var.node_memory_gb
  }

  node_config_details {
    size = var.node_pool_size

    dynamic "placement_configs" {
      for_each = local.ad_names
      content {
        availability_domain = placement_configs.value
        subnet_id           = oci_core_subnet.node_pool.id
      }
    }

    freeform_tags = {
      Project     = "nexus-rag"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }

  node_source_details {
    source_type = "IMAGE"
    image_id    = var.node_image_id
  }

  initial_node_labels {
    key   = "role"
    value = "worker"
  }

  initial_node_labels {
    key   = "project"
    value = "nexus-rag"
  }

  ssh_public_key = var.ssh_public_key
}
