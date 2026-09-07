data "azurerm_client_config" "current" {}

# ============================================================
# PRODUCTION KEY VAULT
#
# Production secrets remain inside the Production subscription.
# Public network access is disabled; workloads reach the vault
# through its Private Endpoint.
# ============================================================

resource "azurerm_key_vault" "prod" {
  provider = azurerm.prod

  name                = "sog-prod-kv"
  location            = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_location
  resource_group_name = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name

  tenant_id = data.azurerm_client_config.current.tenant_id
  sku_name  = "standard"

  rbac_authorization_enabled    = true
  public_network_access_enabled = false

  soft_delete_retention_days = 7
  purge_protection_enabled   = true

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
  }
}

# ============================================================
# PRODUCTION KEY VAULT PRIVATE ENDPOINT
# ============================================================

resource "azurerm_private_endpoint" "prod_key_vault" {
  provider = azurerm.prod

  name                = "prod-keyvault-pe"
  location            = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_location
  resource_group_name = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name

  subnet_id = azurerm_subnet.prod_private_endpoints.id

  private_service_connection {
    name                           = "prod-keyvault-connection"
    private_connection_resource_id = azurerm_key_vault.prod.id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name = "keyvault-dns-zone-group"

    private_dns_zone_ids = [
      azurerm_private_dns_zone.key_vault.id
    ]
  }

  tags = {
    Environment = "production"
    Owner       = "networking-team"
    CostCenter  = "production"
  }
}