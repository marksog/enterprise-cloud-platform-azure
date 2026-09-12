data "terraform_remote_state" "subscriptions" {
  backend = "azurerm"

  config = {
    resource_group_name  = "sog-platform-bootstrap-rg"
    storage_account_name = "sogtfstate001"
    container_name       = "tfstate"
    key                  = "subscriptions.tfstate"
    use_azuread_auth     = true
  }
}

data "terraform_remote_state" "connectivity" {
  backend = "azurerm"

  config = {
    resource_group_name  = "sog-platform-bootstrap-rg"
    storage_account_name = "sogtfstate001"
    container_name       = "tfstate"
    key                  = "connectivity.tfstate"
    use_azuread_auth     = true
  }
}

# ============================================================
# LEGACY HUB NETWORK
# TEMPORARILY RETAINED DURING DNS MIGRATION
# ============================================================

resource "azurerm_resource_group" "hub" {
  name     = "sog-platform-connectivity-rg"
  location = "eastus"

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
  }
}



# ============================================================
# PRODUCTION SPOKE
# ============================================================

resource "azurerm_virtual_network" "prod" {
  provider = azurerm.prod

  name                = "sog-prod-spoke-vnet"
  location            = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_location
  resource_group_name = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name
  address_space       = ["10.10.0.0/20"]

  tags = {
    Environment = "production"
    Owner       = "networking-team"
    CostCenter  = "production"
  }
}

# ============================================================
# NON-PRODUCTION SPOKE
# ============================================================

resource "azurerm_virtual_network" "nonprod" {
  provider = azurerm.nonprod

  name                = "sog-nonprod-spoke-vnet"
  location            = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_location
  resource_group_name = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_name
  address_space       = ["10.20.0.0/20"]

  tags = {
    Environment = "nonproduction"
    Owner       = "networking-team"
    CostCenter  = "nonproduction"
  }
}