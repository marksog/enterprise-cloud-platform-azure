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

output "platform_shared_services_subscription_id" {
  value = "/subscriptions/9ee656be-a9d7-4006-b90f-7549517b1edc"
}

output "platform_connectivity_paid_subscription_id" {
  value = "/subscriptions/2dcbd775-c87b-4099-bb4b-2740850fda0b"
}

output "platform_observability_subscription_id" {
  value = "/subscriptions/1a8e995d-4fc1-485a-b192-562826ca1fc8"
}