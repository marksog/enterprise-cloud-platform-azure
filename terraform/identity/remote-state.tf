# ============================================================
# NETWORK REMOTE STATE
#
# Identity consumes infrastructure information produced by
# the networking layer rather than hardcoding resource IDs.
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