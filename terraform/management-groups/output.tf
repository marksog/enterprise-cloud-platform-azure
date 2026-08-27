output "enterprise_management_group_id" {
  description = "Resource ID of the Enterprise management group."
  value       = azurerm_management_group.enterprise.id
}

output "platform_management_group_id" {
  description = "Resource ID of the Platform management group."
  value       = azurerm_management_group.platform.id
}

output "production_management_group_id" {
  description = "Resource ID of the Production management group."
  value       = azurerm_management_group.production.id
}

output "nonproduction_management_group_id" {
  description = "Resource ID of the Non-Production management group."
  value       = azurerm_management_group.nonproduction.id
}

output "sandbox_management_group_id" {
  description = "Resource ID of the Sandbox management group."
  value       = azurerm_management_group.sandbox.id
}

output "acquisitions_management_group_id" {
  description = "Resource ID of the Acquisitions management group."
  value       = azurerm_management_group.acquisitions.id
}

output "regulated_management_group_id" {
  description = "Resource ID of the Regulated management group."
  value       = azurerm_management_group.regulated.id
}

output "management_group_ids" {
  description = "Map of management group keys to Azure resource IDs."

  value = {
    enterprise    = azurerm_management_group.enterprise.id
    platform      = azurerm_management_group.platform.id
    production    = azurerm_management_group.production.id
    nonproduction = azurerm_management_group.nonproduction.id
    sandbox       = azurerm_management_group.sandbox.id
    acquisitions  = azurerm_management_group.acquisitions.id
    regulated     = azurerm_management_group.regulated.id
  }
}