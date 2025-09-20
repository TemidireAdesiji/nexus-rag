output "cluster_id" {
  description = "OKE cluster OCID"
  value       = oci_containerengine_cluster.nexus.id
}

output "cluster_endpoint" {
  description = "OKE cluster Kubernetes API endpoint"
  value       = oci_containerengine_cluster.nexus.endpoints[0].kubernetes
}

output "cluster_name" {
  description = "OKE cluster name"
  value       = oci_containerengine_cluster.nexus.name
}

output "vcn_id" {
  description = "VCN OCID"
  value       = oci_core_vcn.nexus.id
}

output "node_pool_id" {
  description = "Node pool OCID"
  value       = oci_containerengine_node_pool.nexus.id
}

output "kubeconfig_command" {
  description = "Command to generate kubeconfig for cluster access"
  value       = "oci ce cluster create-kubeconfig --cluster-id ${oci_containerengine_cluster.nexus.id} --file $HOME/.kube/config --region ${var.oci_region}"
}
