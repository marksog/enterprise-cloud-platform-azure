terraform {
  backend "azurerm" {
    resource_group_name  = "sog-platform-bootstrap-rg"
    storage_account_name = "sogtfstate001"
    container_name       = "tfstate"
    key                  = "management-groups.tfstate"
  }
}