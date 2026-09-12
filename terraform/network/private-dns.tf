# ============================================================
# LEGACY PRIVATE DNS ZONE
#
# Temporarily retained during migration so the old DNS records
# are not deleted until Prod/NonProd have successfully moved
# to the new Connectivity-owned DNS zone.
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
# PRODUCTION VNET LINK
# New centralized DNS zone in paid Connectivity subscription.
# ============================================================

resource "azurerm_private_dns_zone_virtual_network_link" "key_vault_prod" {
  provider = azurerm.prod

  name = "keyvault-dns-to-prod"

  private_dns_zone_id = data.terraform_remote_state.connectivity.outputs.key_vault_private_dns_zone_id
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
# New centralized DNS zone in paid Connectivity subscription.
# ============================================================

resource "azurerm_private_dns_zone_virtual_network_link" "key_vault_nonprod" {
  provider = azurerm.nonprod

  name = "keyvault-dns-to-nonprod"

  private_dns_zone_id = data.terraform_remote_state.connectivity.outputs.key_vault_private_dns_zone_id
  virtual_network_id  = azurerm_virtual_network.nonprod.id

  registration_enabled = false

  tags = {
    Environment = "nonproduction"
    Owner       = "networking-team"
    CostCenter  = "nonproduction"
  }
}