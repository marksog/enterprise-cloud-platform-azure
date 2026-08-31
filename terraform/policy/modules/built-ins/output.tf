output "storage_public_access_id" {
  value = data.azurerm_policy_definition.storage_public_access.id
}

output "storage_secure_transfer_id" {
  value = data.azurerm_policy_definition.storage_secure_transfer.id
}

output "storage_minimum_tls_id" {
  value = data.azurerm_policy_definition.storage_minimum_tls.id
}

output "allowed_locations_id" {
  value = data.azurerm_policy_definition.allowed_locations.id
}