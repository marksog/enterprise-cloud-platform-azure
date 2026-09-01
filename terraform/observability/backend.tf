terraform {
  backend "azurerm" {
    resource_group_name  = "sog-platform-bootstrap-rg"
    storage_account_name = "sogtfstate001"
    container_name       = "tfstate"
    key                  = "observability.tfstate"

    use_azuread_auth = true
    use_oidc         = true
  }
}