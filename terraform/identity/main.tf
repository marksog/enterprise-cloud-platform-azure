# ============================================================
# IDENTITY FOUNDATION
#
# Human identity
#   -> Microsoft Entra groups / Azure RBAC
#
# Platform identity
#   -> GitHub Actions OIDC plan/deploy identities
#
# Workload identity
#   -> one user-assigned managed identity per application
#      and environment
# ============================================================

resource "azurerm_resource_group" "prod_identity" {
  provider = azurerm.prod

  name     = "sog-prod-identity-rg"
  location = "westus3"

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
    ManagedBy   = "terraform"
  }
}

resource "azurerm_resource_group" "nonprod_identity" {
  provider = azurerm.nonprod

  name     = "sog-nonprod-identity-rg"
  location = "westus3"

  tags = {
    Environment = "nonproduction"
    Owner       = "platform-team"
    CostCenter  = "nonproduction"
    ManagedBy   = "terraform"
  }
}

locals {
  prod_workload_identities = {
    for name, config in var.workload_identities : name => config
    if config.environment == "production"
  }

  nonprod_workload_identities = {
    for name, config in var.workload_identities : name => config
    if config.environment == "nonproduction"
  }
}

resource "azurerm_user_assigned_identity" "prod_workload" {
  provider = azurerm.prod
  for_each = local.prod_workload_identities

  name                = "sog-${each.key}-prod-id"
  location            = azurerm_resource_group.prod_identity.location
  resource_group_name = azurerm_resource_group.prod_identity.name

  tags = {
    Environment = "production"
    Application = each.key
    Owner       = each.value.owner
    CostCenter  = each.value.cost_center
    ManagedBy   = "terraform"
    Purpose     = "workload-runtime"
  }
}

resource "azurerm_user_assigned_identity" "nonprod_workload" {
  provider = azurerm.nonprod
  for_each = local.nonprod_workload_identities

  name                = "sog-${each.key}-nonprod-id"
  location            = azurerm_resource_group.nonprod_identity.location
  resource_group_name = azurerm_resource_group.nonprod_identity.name

  tags = {
    Environment = "nonproduction"
    Application = each.key
    Owner       = each.value.owner
    CostCenter  = each.value.cost_center
    ManagedBy   = "terraform"
    Purpose     = "workload-runtime"
  }
}