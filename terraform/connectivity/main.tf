resource "azurerm_resource_group" "hub" {
  name     = "sog-platform-connectivity-rg"
  location = "eastus"

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
  }
}

resource "azurerm_virtual_network" "hub" {
  name                = "sog-hub-vnet"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name
  address_space       = ["10.0.0.0/20"]

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
  }
}