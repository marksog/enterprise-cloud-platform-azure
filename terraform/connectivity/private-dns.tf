# ============================================================
# CENTRALIZED PRIVATE DNS
#
# Central Private DNS is now owned by the paid Connectivity
# subscription. Prod and NonProd consume this shared DNS service.
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
# PAID HUB VNET LINK
# ============================================================

resource "azurerm_private_dns_zone_virtual_network_link" "key_vault_hub" {
  name                = "keyvault-dns-to-paid-hub"
  private_dns_zone_id = azurerm_private_dns_zone.key_vault.id
  virtual_network_id  = azurerm_virtual_network.hub.id

  registration_enabled = false

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
  }
}