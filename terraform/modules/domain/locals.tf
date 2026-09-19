# ============================================================
# DOMAIN DERIVED VALUES
#
# Platform-controlled naming and metadata derived from the
# domain's logical name and environment.
# ============================================================

locals {
  resource_prefix = "sog-${var.environment}-${var.name}"

  # Kubernetes namespace contract.
  # GitOps will eventually create this namespace.
  namespace_name = local.resource_prefix

  # Domain-owned Azure Key Vault.
  key_vault_name = "${local.resource_prefix}-kv"

  # Common Kubernetes metadata for resources belonging
  # to this domain.
  common_labels = {
    "sog.io/domain"                = var.name
    "sog.io/environment"           = var.environment
    "app.kubernetes.io/managed-by" = "sog-platform"
  }
}