# ============================================================
# HUB NETWORK OUTPUTS
# ============================================================

output "hub_vnet_id" {
  description = "Resource ID of the central hub virtual network."
  value       = azurerm_virtual_network.hub.id
}


# ============================================================
# PRIVATE DNS OUTPUTS
# ============================================================

output "key_vault_private_dns_zone_id" {
  description = "Resource ID of the centralized Key Vault Private DNS zone."
  value       = azurerm_private_dns_zone.key_vault.id
}