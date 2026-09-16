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

# ============================================================
# PRODUCTION AKS OUTPUTS
# ============================================================

output "prod_aks_id" {
  description = "Resource ID of the Production AKS cluster."
  value       = azurerm_kubernetes_cluster.prod.id
}

output "prod_aks_name" {
  description = "Name of the Production AKS cluster."
  value       = azurerm_kubernetes_cluster.prod.name
}

output "prod_aks_resource_group_name" {
  description = "Resource group containing the Production AKS cluster."
  value       = azurerm_kubernetes_cluster.prod.resource_group_name
}

output "prod_aks_oidc_issuer_url" {
  description = "OIDC issuer URL used by Production AKS Workload Identity."
  value       = azurerm_kubernetes_cluster.prod.oidc_issuer_url
}


# ============================================================
# NON-PRODUCTION AKS OUTPUTS
# ============================================================

output "nonprod_aks_id" {
  description = "Resource ID of the Non-Production AKS cluster."
  value       = azurerm_kubernetes_cluster.nonprod.id
}

output "nonprod_aks_name" {
  description = "Name of the Non-Production AKS cluster."
  value       = azurerm_kubernetes_cluster.nonprod.name
}

output "nonprod_aks_resource_group_name" {
  description = "Resource group containing the Non-Production AKS cluster."
  value       = azurerm_kubernetes_cluster.nonprod.resource_group_name
}

output "nonprod_aks_oidc_issuer_url" {
  description = "OIDC issuer URL used by Non-Production AKS Workload Identity."
  value       = azurerm_kubernetes_cluster.nonprod.oidc_issuer_url
}