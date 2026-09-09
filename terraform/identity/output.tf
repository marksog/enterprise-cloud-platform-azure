# ============================================================
# WORKLOAD IDENTITY OUTPUTS
# Consumed by the platform layer and later by workload
# federation configuration.
# ============================================================

output "prod_workload_identity_id" {
  description = "Resource ID of the Production workload managed identity."
  value       = azurerm_user_assigned_identity.prod_workload.id
}

output "prod_workload_identity_client_id" {
  description = "Client ID of the Production workload managed identity."
  value       = azurerm_user_assigned_identity.prod_workload.client_id
}

output "prod_workload_identity_principal_id" {
  description = "Principal ID of the Production workload managed identity."
  value       = azurerm_user_assigned_identity.prod_workload.principal_id
}

output "nonprod_workload_identity_id" {
  description = "Resource ID of the Non-Production workload managed identity."
  value       = azurerm_user_assigned_identity.nonprod_workload.id
}

output "nonprod_workload_identity_client_id" {
  description = "Client ID of the Non-Production workload managed identity."
  value       = azurerm_user_assigned_identity.nonprod_workload.client_id
}

output "nonprod_workload_identity_principal_id" {
  description = "Principal ID of the Non-Production workload managed identity."
  value       = azurerm_user_assigned_identity.nonprod_workload.principal_id
}