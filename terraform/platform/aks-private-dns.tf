# ============================================================
# AKS PRIVATE DNS — HUB MANAGEMENT ACCESS
#
# Private AKS clusters use Azure-managed Private DNS zones.
#
# The management plane resides in the central Hub VNet.
# Linking the Hub VNet to each AKS Private DNS zone allows
# management hosts to resolve the private Kubernetes API
# endpoints without exposing those APIs publicly.
# ============================================================


# ============================================================
# DERIVE AZURE-MANAGED AKS PRIVATE DNS ZONE NAMES
#
# Example:
#
# private FQDN:
#   sog-nonprod-aks-xxxx.<zone>.privatelink.eastus.azmk8s.io
#
# DNS zone:
#   <zone>.privatelink.eastus.azmk8s.io
#
# AKS generates the zone identifier, so we derive it rather
# than hardcoding a value that can change after cluster
# recreation.
# ============================================================

locals {
  prod_private_fqdn_parts = split(
    ".",
    azurerm_kubernetes_cluster.prod.private_fqdn
  )

  nonprod_private_fqdn_parts = split(
    ".",
    azurerm_kubernetes_cluster.nonprod.private_fqdn
  )

  prod_aks_private_dns_zone_name = join(
    ".",
    slice(
      local.prod_private_fqdn_parts,
      1,
      length(local.prod_private_fqdn_parts)
    )
  )

  nonprod_aks_private_dns_zone_name = join(
    ".",
    slice(
      local.nonprod_private_fqdn_parts,
      1,
      length(local.nonprod_private_fqdn_parts)
    )
  )
}


# ============================================================
# DISCOVER AZURE-MANAGED PRIVATE DNS ZONES
#
# The zones live inside the AKS-managed MC_* resource groups.
# ============================================================

data "azurerm_private_dns_zone" "prod_aks" {
  provider = azurerm.prod

  name                = local.prod_aks_private_dns_zone_name
  resource_group_name = azurerm_kubernetes_cluster.prod.node_resource_group
}

data "azurerm_private_dns_zone" "nonprod_aks" {
  provider = azurerm.nonprod

  name                = local.nonprod_aks_private_dns_zone_name
  resource_group_name = azurerm_kubernetes_cluster.nonprod.node_resource_group
}


# ============================================================
# LINK HUB VNET TO PROD AKS PRIVATE DNS
# ============================================================

resource "azurerm_private_dns_zone_virtual_network_link" "prod_aks_hub" {
  provider = azurerm.prod

  name = "sog-hub-to-prod-aks"

  resource_group_name   = azurerm_kubernetes_cluster.prod.node_resource_group
  private_dns_zone_name = data.azurerm_private_dns_zone.prod_aks.name

  virtual_network_id = data.terraform_remote_state.connectivity.outputs.hub_vnet_id

  registration_enabled = false

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
    Purpose     = "aks-management-access"
    ManagedBy   = "terraform"
  }
}


# ============================================================
# LINK HUB VNET TO NONPROD AKS PRIVATE DNS
# ============================================================

resource "azurerm_private_dns_zone_virtual_network_link" "nonprod_aks_hub" {
  provider = azurerm.nonprod

  name = "sog-hub-to-nonprod-aks"

  resource_group_name   = azurerm_kubernetes_cluster.nonprod.node_resource_group
  private_dns_zone_name = data.azurerm_private_dns_zone.nonprod_aks.name

  virtual_network_id = data.terraform_remote_state.connectivity.outputs.hub_vnet_id

  registration_enabled = false

  tags = {
    Environment = "nonproduction"
    Owner       = "platform-team"
    CostCenter  = "nonproduction"
    Purpose     = "aks-management-access"
    ManagedBy   = "terraform"
  }
}