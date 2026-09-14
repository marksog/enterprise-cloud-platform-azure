# ============================================================
# SHARED CONTAINER REGISTRY OUTPUTS
# ============================================================

output "shared_acr_id" {
  description = "Resource ID of the shared Azure Container Registry."
  value       = azurerm_container_registry.shared.id
}

output "shared_acr_name" {
  description = "Name of the shared Azure Container Registry."
  value       = azurerm_container_registry.shared.name
}

output "shared_acr_login_server" {
  description = "Login server for the shared Azure Container Registry."
  value       = azurerm_container_registry.shared.login_server
}