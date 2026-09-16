# ============================================================
# AKS HUMAN ADMINISTRATIVE ACCESS
#
# Human authorization is assigned to Microsoft Entra security
# groups rather than individual users.
#
# Group membership remains an identity-governance concern.
# This stack controls which approved groups receive AKS
# data-plane administrative authorization.
# ============================================================


# ------------------------------------------------------------
# NON-PRODUCTION AKS ADMINISTRATORS
# ------------------------------------------------------------

resource "azurerm_role_assignment" "nonprod_aks_admin" {
  provider = azurerm.nonprod

  for_each = var.nonprod_aks_admin_group_object_ids

  scope                = azurerm_kubernetes_cluster.nonprod.id
  role_definition_name = "Azure Kubernetes Service RBAC Cluster Admin"

  principal_id   = each.value
  principal_type = "Group"
}


# ------------------------------------------------------------
# PRODUCTION AKS ADMINISTRATORS
# ------------------------------------------------------------

resource "azurerm_role_assignment" "prod_aks_admin" {
  provider = azurerm.prod

  for_each = var.prod_aks_admin_group_object_ids

  scope                = azurerm_kubernetes_cluster.prod.id
  role_definition_name = "Azure Kubernetes Service RBAC Cluster Admin"

  principal_id   = each.value
  principal_type = "Group"
}