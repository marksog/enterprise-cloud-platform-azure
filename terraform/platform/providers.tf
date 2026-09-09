provider "azurerm" {
  features {}

  use_oidc = true
}

provider "azurerm" {
  alias = "prod"

  features {}

  subscription_id = var.prod_subscription_id
  use_oidc        = true
}

provider "azurerm" {
  alias = "nonprod"

  features {}

  subscription_id = var.nonprod_subscription_id
  use_oidc        = true
}