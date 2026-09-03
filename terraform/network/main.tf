# ============================================================
# HUB NETWORK
# Subscription: platform-connectivity
# Address space: 10.0.0.0/20
# ============================================================

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


# ============================================================
# PRODUCTION SPOKE
# Subscription: Production
# Address space: 10.10.0.0/20
# ============================================================

resource "azurerm_resource_group" "prod_network" {
  provider = azurerm.prod

  name     = "sog-prod-network-rg"
  location = "eastus"

  tags = {
    Environment = "production"
    Owner       = "networking-team"
    CostCenter  = "production"
  }
}

resource "azurerm_virtual_network" "prod" {
  provider = azurerm.prod

  name                = "sog-prod-spoke-vnet"
  location            = azurerm_resource_group.prod_network.location
  resource_group_name = azurerm_resource_group.prod_network.name
  address_space       = ["10.10.0.0/20"]

  tags = {
    Environment = "production"
    Owner       = "networking-team"
    CostCenter  = "production"
  }
}


# ============================================================
# NON-PRODUCTION SPOKE
# Subscription: Non-Production
# Address space: 10.20.0.0/20
# ============================================================

resource "azurerm_resource_group" "nonprod_network" {
  provider = azurerm.nonprod

  name     = "sog-nonprod-network-rg"
  location = "eastus"

  tags = {
    Environment = "nonproduction"
    Owner       = "networking-team"
    CostCenter  = "nonproduction"
  }
}

resource "azurerm_virtual_network" "nonprod" {
  provider = azurerm.nonprod

  name                = "sog-nonprod-spoke-vnet"
  location            = azurerm_resource_group.nonprod_network.location
  resource_group_name = azurerm_resource_group.nonprod_network.name
  address_space       = ["10.20.0.0/20"]

  tags = {
    Environment = "nonproduction"
    Owner       = "networking-team"
    CostCenter  = "nonproduction"
  }
}