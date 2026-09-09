# ============================================================
# KEY VAULT OUTPUTS
# Consumed by downstream identity/platform layers.
# ============================================================

output "prod_key_vault_id" {
  description = "Resource ID of the Production Key Vault."
  value       = azurerm_key_vault.prod.id
}

output "nonprod_key_vault_id" {
  description = "Resource ID of the Non-Production Key Vault."
  value       = azurerm_key_vault.nonprod.id
}

output "prod_key_vault_name" {
  description = "Name of the Production Key Vault."
  value       = azurerm_key_vault.prod.name
}

output "nonprod_key_vault_name" {
  description = "Name of the Non-Production Key Vault."
  value       = azurerm_key_vault.nonprod.name
}

output "prod_aks_subnet_id" {
  description = "Resource ID of the Production AKS subnet."
  value       = azurerm_subnet.prod_aks.id
}

output "nonprod_aks_subnet_id" {
  description = "Resource ID of the Non-Production AKS subnet."
  value       = azurerm_subnet.nonprod_aks.id
}

# ============================================================
# SPOKE LOCATION OUTPUTS
# Consumed by downstream platform resources that must be
# colocated with networking resources such as AKS node pools.
# ============================================================

output "prod_spoke_location" {
  description = "Azure region of the Production spoke virtual network."
  value       = azurerm_virtual_network.prod.location
}

output "nonprod_spoke_location" {
  description = "Azure region of the Non-Production spoke virtual network."
  value       = azurerm_virtual_network.nonprod.location
}