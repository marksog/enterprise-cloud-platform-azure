output "resource_group_name" {
  description = "Resource group containing the Terraform state backend."
  value       = azurerm_resource_group.bootstrap.name
}

output "storage_account_name" {
  description = "Storage account used for Terraform remote state."
  value       = azurerm_storage_account.bootstrap.name
}

output "container_name" {
  description = "Blob container used for Terraform state."
  value       = azurerm_storage_container.bootstrap.name
}

output "storage_account_id" {
  description = "Resource ID of the Terraform state storage account."
  value       = azurerm_storage_account.bootstrap.id
}