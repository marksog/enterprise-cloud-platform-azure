resource "azurerm_resource_group" "bootstrap" {
  name     = local.resource_group_name
  location = var.location
  tags     = local.common_tags
}

resource "azurerm_storage_account" "bootstrap" {
  name                          = local.storage_account_name
  resource_group_name           = azurerm_resource_group.bootstrap.name
  location                      = azurerm_resource_group.bootstrap.location
  account_tier                  = var.account_tier
  account_replication_type      = var.account_replication_type
  https_traffic_only_enabled    = var.https_traffic_only_enabled
  public_network_access_enabled = true
  allow_nested_items_to_be_public = false

  network_rules {
    default_action = "Deny"

    ip_rules = [
      var.bootstrap_allowed_ip
    ]
  }

  blob_properties {
    versioning_enabled = true

    delete_retention_policy {
      days = 14
    }

    container_delete_retention_policy {
      days = 14
    }
  }

  tags = local.common_tags
}

resource "azurerm_storage_container" "bootstrap" {
  name                  = local.container_name
  storage_account_id    = azurerm_storage_account.bootstrap.id
  container_access_type = "private"
}