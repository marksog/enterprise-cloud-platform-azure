# ============================================================
# IDENTITY RESOURCE GROUPS
#
# Workload identities are separated from networking resources
# and remain inside their respective environment subscriptions.
# ============================================================

resource "azurerm_resource_group" "prod_identity" {
  provider = azurerm.prod

  name     = "sog-prod-identity-rg"
  location = "westus3"

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
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
  }
}


# ============================================================
# PRODUCTION WORKLOAD MANAGED IDENTITY
#
# Later federated to a Kubernetes ServiceAccount through
# AKS Workload Identity.
# ============================================================

resource "azurerm_user_assigned_identity" "prod_workload" {
  provider = azurerm.prod

  name                = "sog-prod-workload-identity"
  location            = azurerm_resource_group.prod_identity.location
  resource_group_name = azurerm_resource_group.prod_identity.name

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
  }
}


# ============================================================
# NON-PRODUCTION WORKLOAD MANAGED IDENTITY
# ============================================================

resource "azurerm_user_assigned_identity" "nonprod_workload" {
  provider = azurerm.nonprod

  name                = "sog-nonprod-workload-identity"
  location            = azurerm_resource_group.nonprod_identity.location
  resource_group_name = azurerm_resource_group.nonprod_identity.name

  tags = {
    Environment = "nonproduction"
    Owner       = "platform-team"
    CostCenter  = "nonproduction"
  }
}


# ============================================================
# KEY VAULT RBAC
#
# Runtime identities receive read access to secrets only.
# They do not receive permission to create/delete secrets or
# administer the Key Vault.
# ============================================================

resource "azurerm_role_assignment" "prod_workload_key_vault_secrets" {
  provider = azurerm.prod

  scope                = data.terraform_remote_state.network.outputs.prod_key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.prod_workload.principal_id
}

resource "azurerm_role_assignment" "nonprod_workload_key_vault_secrets" {
  provider = azurerm.nonprod

  scope                = data.terraform_remote_state.network.outputs.nonprod_key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.nonprod_workload.principal_id
}