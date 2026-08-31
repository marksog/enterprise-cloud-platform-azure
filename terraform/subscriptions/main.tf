data "terraform_remote_state" "management_groups" {
  backend = "azurerm"

  config = {
    resource_group_name  = "sog-platform-bootstrap-rg"
    storage_account_name = "sogtfstate001"
    container_name       = "tfstate"
    key                  = "management-groups.tfstate"

    use_oidc         = true
    use_azuread_auth = true
  }
}

resource "azurerm_management_group_subscription_association" "subscriptions" {
  for_each = local.subscriptions

  management_group_id = each.value.management_group_id
  subscription_id     = each.value.subscription_id
}