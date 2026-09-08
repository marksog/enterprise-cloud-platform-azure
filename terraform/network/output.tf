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