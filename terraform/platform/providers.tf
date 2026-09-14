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

provider "azurerm" {
  alias = "shared_services"

  features {}

  subscription_id = trimprefix(
    data.terraform_remote_state.subscriptions.outputs.platform_shared_services_subscription_id,
    "/subscriptions/"
  )

  use_oidc = true
}


# ============================================================
# CURRENT AZURE AUTHENTICATION CONTEXT
#
# Used to derive tenant-level information without hardcoding
# the Microsoft Entra tenant ID into platform resources.
# ============================================================

data "azurerm_client_config" "current" {}