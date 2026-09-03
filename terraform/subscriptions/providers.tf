provider "azurerm" {
  features {}

  subscription_id = "4eeb7aa0-684a-473d-9ae3-f238dfc3f944"
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