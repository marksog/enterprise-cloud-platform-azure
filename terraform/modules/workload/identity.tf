# ============================================================
# WORKLOAD IDENTITY
#
# Each workload receives its own Azure user-assigned managed
# identity.
#
# AKS Workload Identity allows the workload's Kubernetes
# ServiceAccount to authenticate as this Azure identity without
# storing client secrets in Kubernetes.
# ============================================================


# ------------------------------------------------------------
# AZURE MANAGED IDENTITY
#
# Represents this workload in Azure.
# ------------------------------------------------------------

resource "azurerm_user_assigned_identity" "this" {
  name                = local.managed_identity_name
  location            = var.azure_location
  resource_group_name = var.azure_resource_group_name

  tags = local.common_azure_tags
}


# ------------------------------------------------------------
# FEDERATED IDENTITY CREDENTIAL
#
# Establishes trust between the workload's Kubernetes
# ServiceAccount and its Azure managed identity.
#
# The trust is restricted by:
#
#   issuer   -> this specific AKS OIDC issuer
#   subject  -> this specific Kubernetes ServiceAccount
#   audience -> Azure token exchange
# ------------------------------------------------------------

resource "azurerm_federated_identity_credential" "this" {
  name                      = "${var.name}-aks-federation"
  user_assigned_identity_id = azurerm_user_assigned_identity.this.id

  issuer = var.aks_oidc_issuer_url

  subject = "system:serviceaccount:${var.namespace_name}:${local.service_account_name}"

  audience = [
    "api://AzureADTokenExchange"
  ]
}


# ------------------------------------------------------------
# DOMAIN SECRET STORE AUTHORIZATION
#
# When the workload belongs to a domain with secret storage
# enabled, its managed identity receives permission to read
# secrets from that domain's Key Vault.
#
# The boolean controls resource creation because it is known
# during Terraform planning.
#
# The Key Vault resource ID may remain unknown until apply;
# that is acceptable because it is used as configuration,
# not to determine resource count.
# ------------------------------------------------------------

resource "azurerm_role_assignment" "domain_secret_reader" {
  count = var.domain_secret_store_enabled ? 1 : 0

  scope                = var.domain_key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.this.principal_id
  principal_type       = "ServicePrincipal"
}