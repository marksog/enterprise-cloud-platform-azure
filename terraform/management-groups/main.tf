resource "azurerm_management_group" "enterprise" {
  name         = local.management_groups["enterprise"].name
  display_name = local.management_groups["enterprise"].display_name
}

resource "azurerm_management_group" "platform" {
  name                       = local.management_groups["platform"].name
  display_name               = local.management_groups["platform"].display_name
  parent_management_group_id = azurerm_management_group.enterprise.id
}

resource "azurerm_management_group" "production" {
  name                       = local.management_groups["production"].name
  display_name               = local.management_groups["production"].display_name
  parent_management_group_id = azurerm_management_group.enterprise.id
}

resource "azurerm_management_group" "nonproduction" {
  name                       = local.management_groups["nonproduction"].name
  display_name               = local.management_groups["nonproduction"].display_name
  parent_management_group_id = azurerm_management_group.enterprise.id
}

resource "azurerm_management_group" "sandbox" {
  name                       = local.management_groups["sandbox"].name
  display_name               = local.management_groups["sandbox"].display_name
  parent_management_group_id = azurerm_management_group.enterprise.id
}

resource "azurerm_management_group" "acquisitions" {
  name                       = local.management_groups["acquisitions"].name
  display_name               = local.management_groups["acquisitions"].display_name
  parent_management_group_id = azurerm_management_group.enterprise.id
}

resource "azurerm_management_group" "regulated" {
  name                       = local.management_groups["regulated"].name
  display_name               = local.management_groups["regulated"].display_name
  parent_management_group_id = azurerm_management_group.production.id
}