# ============================================================
# NETWORK REMOTE STATE
#
# Platform consumes networking resources rather than
# recreating or hardcoding them.
# ============================================================

data "terraform_remote_state" "network" {
  backend = "azurerm"

  config = {
    resource_group_name  = "sog-platform-bootstrap-rg"
    storage_account_name = "sogtfstate001"
    container_name       = "tfstate"
    key                  = "networking.tfstate"

    use_azuread_auth = true
    use_oidc         = true
  }
}


# ============================================================
# IDENTITY REMOTE STATE
#
# Platform will consume managed identity information produced
# by the identity layer.
# ============================================================

data "terraform_remote_state" "identity" {
  backend = "azurerm"

  config = {
    resource_group_name  = "sog-platform-bootstrap-rg"
    storage_account_name = "sogtfstate001"
    container_name       = "tfstate"
    key                  = "identity.tfstate"

    use_azuread_auth = true
    use_oidc         = true
  }
}