# ============================================================
# DOMAIN SECRET STORE
#
# A domain may receive a dedicated Azure Key Vault.
# The domain module owns the vault and its Private Endpoint.
#
# Networking and DNS topology are supplied by the environment
# root through approved module inputs.
# ============================================================

resource "azurerm_key_vault" "this" {
  count = var.secret_store_enabled ? 1 : 0

  name                = local.key_vault_name
  location            = var.azure_location
  resource_group_name = var.azure_resource_group_name
  tenant_id           = var.tenant_id

  sku_name = "standard"

  rbac_authorization_enabled = true

  public_network_access_enabled = false

  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  tags = {
    Environment = var.environment
    Domain      = var.name
    ManagedBy   = "terraform"
  }
}


# ============================================================
# DOMAIN KEY VAULT PRIVATE ENDPOINT
# ============================================================

resource "azurerm_private_endpoint" "key_vault" {
  count = var.secret_store_enabled ? 1 : 0

  name                = "${local.resource_prefix}-kv-pe"
  location            = var.azure_location
  resource_group_name = var.azure_resource_group_name
  subnet_id           = var.private_endpoint_subnet_id

  private_service_connection {
    name                           = "${local.resource_prefix}-kv-connection"
    private_connection_resource_id = azurerm_key_vault.this[0].id
    subresource_names              = ["vault"]
    is_manual_connection           = false
  }

  private_dns_zone_group {
    name = "key-vault-dns"

    private_dns_zone_ids = [
      var.key_vault_private_dns_zone_id
    ]
  }

  tags = {
    Environment = var.environment
    Domain      = var.name
    ManagedBy   = "terraform"
  }
}