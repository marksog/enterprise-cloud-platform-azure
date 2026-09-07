# ============================================================
# CENTRALIZED PRIVATE DNS
#
# Shared DNS capability hosted in the Hub / connectivity layer.
# Prod and NonProd keep their own private endpoints and resources,
# but both VNets can resolve Azure Private Link names through
# this central Private DNS zone.
# ============================================================

resource "azurerm_private_dns_zone" "key_vault" {
  name                = "privatelink.vaultcore.azure.net"
  resource_group_name = azurerm_resource_group.hub.name

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
  }
}


# ============================================================
# HUB VNET LINK
# Allows the Hub VNet to resolve records in the Private DNS zone.
# ============================================================

resource "azurerm_private_dns_zone_virtual_network_link" "key_vault_hub" {
  name                = "keyvault-dns-to-hub"
  private_dns_zone_id = azurerm_private_dns_zone.key_vault.id
  virtual_network_id  = azurerm_virtual_network.hub.id

  registration_enabled = false

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
  }
}


# ============================================================
# PRODUCTION VNET LINK
# Allows Prod workloads to resolve Key Vault private endpoints.
# ============================================================

resource "azurerm_private_dns_zone_virtual_network_link" "key_vault_prod" {
  name = "keyvault-dns-to-prod"

  private_dns_zone_id = azurerm_private_dns_zone.key_vault.id
  virtual_network_id  = azurerm_virtual_network.prod.id

  registration_enabled = false

  tags = {
    Environment = "production"
    Owner       = "networking-team"
    CostCenter  = "production"
  }
}


# ============================================================
# NON-PRODUCTION VNET LINK
# Allows NonProd workloads to resolve Key Vault private endpoints.
# ============================================================

resource "azurerm_private_dns_zone_virtual_network_link" "key_vault_nonprod" {
  name = "keyvault-dns-to-nonprod"

  private_dns_zone_id = azurerm_private_dns_zone.key_vault.id
  virtual_network_id  = azurerm_virtual_network.nonprod.id

  registration_enabled = false

  tags = {
    Environment = "nonproduction"
    Owner       = "networking-team"
    CostCenter  = "nonproduction"
  }
}