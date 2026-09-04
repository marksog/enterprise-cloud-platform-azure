# ============================================================
# HUB SUBNETS
# VNet: sog-hub-vnet
# Address space: 10.0.0.0/20
# ============================================================

resource "azurerm_subnet" "hub_firewall" {
  name                 = "AzureFirewallSubnet"
  resource_group_name  = azurerm_resource_group.hub.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = ["10.0.0.0/26"]
}

resource "azurerm_subnet" "hub_bastion" {
  name                 = "AzureBastionSubnet"
  resource_group_name  = azurerm_resource_group.hub.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = ["10.0.0.64/26"]
}

resource "azurerm_subnet" "hub_gateway" {
  name                 = "GatewaySubnet"
  resource_group_name  = azurerm_resource_group.hub.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = ["10.0.0.128/27"]
}

resource "azurerm_subnet" "hub_shared_services" {
  name                 = "shared-services-subnet"
  resource_group_name  = azurerm_resource_group.hub.name
  virtual_network_name = azurerm_virtual_network.hub.name
  address_prefixes     = ["10.0.0.160/27"]
}


# ============================================================
# PRODUCTION SUBNETS
# VNet: sog-prod-spoke-vnet
# Address space: 10.10.0.0/20
# ============================================================

resource "azurerm_subnet" "prod_app" {
  provider = azurerm.prod

  name                 = "prod-app-subnet"
  resource_group_name  = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name
  virtual_network_name = azurerm_virtual_network.prod.name
  address_prefixes     = ["10.10.0.0/24"]
}

resource "azurerm_subnet" "prod_data" {
  provider = azurerm.prod

  name                 = "prod-data-subnet"
  resource_group_name  = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name
  virtual_network_name = azurerm_virtual_network.prod.name
  address_prefixes     = ["10.10.1.0/24"]
}

resource "azurerm_subnet" "prod_private_endpoints" {
  provider = azurerm.prod

  name                 = "prod-private-endpoints"
  resource_group_name  = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name
  virtual_network_name = azurerm_virtual_network.prod.name
  address_prefixes     = ["10.10.2.0/24"]
}

resource "azurerm_subnet" "prod_aks" {
  provider = azurerm.prod

  name                 = "prod-aks-subnet"
  resource_group_name  = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name
  virtual_network_name = azurerm_virtual_network.prod.name
  address_prefixes     = ["10.10.3.0/24"]
}


# ============================================================
# NON-PRODUCTION SUBNETS
# VNet: sog-nonprod-spoke-vnet
# Address space: 10.20.0.0/20
# ============================================================

resource "azurerm_subnet" "nonprod_app" {
  provider = azurerm.nonprod

  name                 = "nonprod-app-subnet"
  resource_group_name  = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_name
  virtual_network_name = azurerm_virtual_network.nonprod.name
  address_prefixes     = ["10.20.0.0/24"]
}

resource "azurerm_subnet" "nonprod_data" {
  provider = azurerm.nonprod

  name                 = "nonprod-data-subnet"
  resource_group_name  = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_name
  virtual_network_name = azurerm_virtual_network.nonprod.name
  address_prefixes     = ["10.20.1.0/24"]
}

resource "azurerm_subnet" "nonprod_private_endpoints" {
  provider = azurerm.nonprod

  name                 = "nonprod-private-endpoints"
  resource_group_name  = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_name
  virtual_network_name = azurerm_virtual_network.nonprod.name
  address_prefixes     = ["10.20.2.0/24"]
}

resource "azurerm_subnet" "nonprod_aks" {
  provider = azurerm.nonprod

  name                 = "nonprod-aks-subnet"
  resource_group_name  = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_name
  virtual_network_name = azurerm_virtual_network.nonprod.name
  address_prefixes     = ["10.20.3.0/24"]
}