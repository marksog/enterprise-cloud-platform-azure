output "log_analytics_workspace_id" {
  value = azurerm_log_analytics_workspace.central.id
}

output "log_analytics_workspace_name" {
  value = azurerm_log_analytics_workspace.central.name
}

output "resource_group_name" {
  value = azurerm_resource_group.observability.name
}