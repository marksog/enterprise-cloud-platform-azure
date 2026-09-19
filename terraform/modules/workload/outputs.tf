output "namespace_name" {
  description = "Platform-derived Kubernetes namespace for the workload."
  value       = var.namespace_name
}

output "service_name" {
  description = "Platform-derived Kubernetes Service name."
  value       = local.service_name
}

output "service_account_name" {
  description = "Platform-derived Kubernetes ServiceAccount name."
  value       = local.service_account_name
}

output "managed_identity_name" {
  description = "Platform-derived Azure managed identity name."
  value       = local.managed_identity_name
}

output "size_profile" {
  description = "Resolved platform capacity profile."
  value       = local.workload_profile
}

output "managed_identity_client_id" {
  description = "Client ID of the Azure managed identity used by AKS Workload Identity."
  value       = azurerm_user_assigned_identity.this.client_id
}

output "managed_identity_principal_id" {
  description = "Principal ID used when assigning Azure RBAC permissions to the workload identity."
  value       = azurerm_user_assigned_identity.this.principal_id
}

output "federated_identity_subject" {
  description = "Kubernetes ServiceAccount subject trusted by the Azure federated identity credential."
  value       = azurerm_federated_identity_credential.this.subject
}