resource "azurerm_resource_group" "observability" {
  name     = "sog-platform-observability-rg"
  location = "eastus"

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
  }
}

resource "azurerm_log_analytics_workspace" "central" {
  name                = "sog-central-observability-law"
  location            = azurerm_resource_group.observability.location
  resource_group_name = azurerm_resource_group.observability.name

  sku               = "PerGB2018"
  retention_in_days = 30

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
  }
}