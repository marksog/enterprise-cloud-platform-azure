data "azurerm_client_config" "current" {
}

module "domain" {
  for_each = var.domains

  source = "../../modules/domain"

  # Domain intent
  name                 = each.key
  secret_store_enabled = each.value.secret_store_enabled

  # Environment context
  environment = "nonprod"

  # Azure context
  azure_location            = data.terraform_remote_state.platform.outputs.nonprod_aks_location
  azure_resource_group_name = data.terraform_remote_state.platform.outputs.nonprod_aks_resource_group_name
  tenant_id                 = data.azurerm_client_config.current.tenant_id

  # Private connectivity supplied by upstream contracts
  private_endpoint_subnet_id = data.terraform_remote_state.network.outputs.nonprod_private_endpoints_subnet_id

  key_vault_private_dns_zone_id = data.terraform_remote_state.connectivity.outputs.key_vault_private_dns_zone_id
}