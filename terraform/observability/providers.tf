provider "azurerm" {
  features {}

  subscription_id = "1a8e995d-4fc1-485a-b192-562826ca1fc8"
}

provider "azurerm" {
  alias = "prod"

  features {}

  subscription_id = "e3bda1e9-e6e9-45a5-b2ee-d3d7a754b594"
}

provider "azurerm" {
  alias = "nonprod"

  features {}

  subscription_id = "4eeb7aa0-684a-473d-9ae3-f238dfc3f944"
}