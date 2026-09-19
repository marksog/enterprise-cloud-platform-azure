output "namespace_name" {
  description = "Platform-derived Kubernetes namespace for the domain."
  value       = local.namespace_name
}

output "domain_name" {
  description = "Logical domain represented by this module."
  value       = var.name
}

output "key_vault_id" {
  description = "Resource ID of the domain Key Vault, or null when secret storage is disabled."
  value       = var.secret_store_enabled ? azurerm_key_vault.this[0].id : null
}

output "key_vault_name" {
  description = "Name of the domain Key Vault, or null when secret storage is disabled."
  value       = var.secret_store_enabled ? azurerm_key_vault.this[0].name : null
}

output "key_vault_private_endpoint_id" {
  description = "Resource ID of the domain Key Vault Private Endpoint, or null when secret storage is disabled."
  value       = var.secret_store_enabled ? azurerm_private_endpoint.key_vault[0].id : null
}