output "prod_network_resource_group_name" {
  value = azurerm_resource_group.prod_network.name
}

output "prod_network_resource_group_location" {
  value = azurerm_resource_group.prod_network.location
}

output "nonprod_network_resource_group_name" {
  value = azurerm_resource_group.nonprod_network.name
}

output "nonprod_network_resource_group_location" {
  value = azurerm_resource_group.nonprod_network.location
}