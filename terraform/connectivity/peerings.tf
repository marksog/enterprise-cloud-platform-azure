# ============================================================
# EXISTING SPOKE VNET LOOKUPS
# ============================================================

data "azurerm_virtual_network" "prod" {
  provider = azurerm.prod

  name                = "sog-prod-spoke-vnet"
  resource_group_name = "sog-prod-network-rg"
}

data "azurerm_virtual_network" "nonprod" {
  provider = azurerm.nonprod

  name                = "sog-nonprod-spoke-vnet"
  resource_group_name = "sog-nonprod-network-rg"
}


# ============================================================
# NEW PAID HUB <-> PROD
# ============================================================

resource "azurerm_virtual_network_peering" "paid_hub_to_prod" {
  name = "paid-hub-to-prod"

  resource_group_name       = azurerm_resource_group.hub.name
  virtual_network_name      = azurerm_virtual_network.hub.name
  remote_virtual_network_id = data.azurerm_virtual_network.prod.id

  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  use_remote_gateways          = false
}

resource "azurerm_virtual_network_peering" "prod_to_paid_hub" {
  provider = azurerm.prod

  name = "prod-to-paid-hub"

  resource_group_name       = "sog-prod-network-rg"
  virtual_network_name      = data.azurerm_virtual_network.prod.name
  remote_virtual_network_id = azurerm_virtual_network.hub.id

  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  use_remote_gateways          = false
}


# ============================================================
# NEW PAID HUB <-> NONPROD
# ============================================================

resource "azurerm_virtual_network_peering" "paid_hub_to_nonprod" {
  name = "paid-hub-to-nonprod"

  resource_group_name       = azurerm_resource_group.hub.name
  virtual_network_name      = azurerm_virtual_network.hub.name
  remote_virtual_network_id = data.azurerm_virtual_network.nonprod.id

  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  use_remote_gateways          = false
}

resource "azurerm_virtual_network_peering" "nonprod_to_paid_hub" {
  provider = azurerm.nonprod

  name = "nonprod-to-paid-hub"

  resource_group_name       = "sog-nonprod-network-rg"
  virtual_network_name      = data.azurerm_virtual_network.nonprod.name
  remote_virtual_network_id = azurerm_virtual_network.hub.id

  allow_virtual_network_access = true
  allow_forwarded_traffic      = true
  use_remote_gateways          = false
}