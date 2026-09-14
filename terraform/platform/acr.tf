# ============================================================
# SHARED AZURE CONTAINER REGISTRY
#
# The registry is a cross-environment platform capability.
#
# Ownership:
#   platform-shared-services subscription
#
# Artifact model:
#   Build once -> validate -> publish once -> promote the same
#   immutable artifact through NonProd and Production.
#
# Access model:
#   CI/CD       -> push
#   NonProd AKS -> pull
#   Prod AKS    -> pull
#   Developers  -> no direct push access
# ============================================================


# ============================================================
# SHARED SERVICES RESOURCE GROUP
# ============================================================

resource "azurerm_resource_group" "shared_services" {
  provider = azurerm.shared_services

  name     = "sog-platform-shared-services-rg"
  location = "eastus"

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
    ManagedBy   = "terraform"
    Purpose     = "shared-platform-services"
  }
}


# ============================================================
# SHARED CONTAINER REGISTRY
#
# Standard is intentionally used for the current lab.
#
# We can later move to Premium when we introduce:
#   - ACR Private Endpoint
#   - private DNS
#   - geo-replication
#   - stronger network isolation
# ============================================================

resource "azurerm_container_registry" "shared" {
  provider = azurerm.shared_services

  name                = "sogplatformacr"
  resource_group_name = azurerm_resource_group.shared_services.name
  location            = azurerm_resource_group.shared_services.location

  sku           = "Standard"
  admin_enabled = false

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
    ManagedBy   = "terraform"
    Purpose     = "container-artifact-registry"
  }
}


# ============================================================
# PRODUCTION AKS -> ACR PULL
#
# AKS kubelet identity is granted pull-only access.
#
# This allows nodes to retrieve container images without
# granting application developers direct registry privileges.
# ============================================================

resource "azurerm_role_assignment" "prod_aks_acr_pull" {
  provider = azurerm.shared_services

  scope                = azurerm_container_registry.shared.id
  role_definition_name = "AcrPull"

  principal_id = azurerm_kubernetes_cluster.prod.kubelet_identity[0].object_id
}


# ============================================================
# NON-PRODUCTION AKS -> ACR PULL
# ============================================================

resource "azurerm_role_assignment" "nonprod_aks_acr_pull" {
  provider = azurerm.shared_services

  scope                = azurerm_container_registry.shared.id
  role_definition_name = "AcrPull"

  principal_id = azurerm_kubernetes_cluster.nonprod.kubelet_identity[0].object_id
}