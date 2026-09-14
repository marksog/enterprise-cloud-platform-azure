# ============================================================
# PLATFORM RESOURCE GROUPS
# ============================================================

resource "azurerm_resource_group" "prod_platform" {
  provider = azurerm.prod

  name     = "sog-prod-platform-rg"
  location = "westus3"

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
    ManagedBy   = "terraform"
  }
}

resource "azurerm_resource_group" "nonprod_platform" {
  provider = azurerm.nonprod

  name     = "sog-nonprod-platform-rg"
  location = "westus3"

  tags = {
    Environment = "nonproduction"
    Owner       = "platform-team"
    CostCenter  = "nonproduction"
    ManagedBy   = "terraform"
  }
}


# ============================================================
# PRODUCTION AKS CLUSTER
#
# Production runtime design:
#
# - Private Kubernetes API
# - Azure CNI
# - Azure Network Policy
# - Centralized egress through UDR/NVA
# - OIDC issuer
# - AKS Workload Identity
# - Microsoft Entra / Azure RBAC
# - Dedicated autoscaled system node pool
# - Separate autoscaled application node pool
# ============================================================

resource "azurerm_kubernetes_cluster" "prod" {
  provider = azurerm.prod

  name                = "sog-prod-aks"
  location            = data.terraform_remote_state.network.outputs.prod_spoke_location
  resource_group_name = azurerm_resource_group.prod_platform.name
  dns_prefix          = "sog-prod-aks"

  private_cluster_enabled = true

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  role_based_access_control_enabled = true

  azure_active_directory_role_based_access_control {
    azure_rbac_enabled = true
    tenant_id          = data.azurerm_client_config.current.tenant_id
  }

  # ----------------------------------------------------------
  # SYSTEM NODE POOL
  #
  # Reserved for critical Kubernetes/platform services.
  # Application workloads should run on separate user pools.
  #
  # Production keeps at least two system nodes for greater
  # resilience during node failure, maintenance, and upgrades.
  # ----------------------------------------------------------

  default_node_pool {
    name = "system"

    vm_size = "Standard_D2s_v5"

    auto_scaling_enabled = true
    min_count            = 2
    max_count            = 3

    only_critical_addons_enabled = true

    vnet_subnet_id = data.terraform_remote_state.network.outputs.prod_aks_subnet_id

    type = "VirtualMachineScaleSets"

    tags = {
      Environment = "production"
      Owner       = "platform-team"
      CostCenter  = "production"
      ManagedBy   = "terraform"
      NodePool    = "system"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "azure"

    # Internet-bound workload traffic follows our centralized
    # egress architecture instead of using an AKS-managed
    # outbound path.
    outbound_type = "userDefinedRouting"

    service_cidr   = "10.110.0.0/16"
    dns_service_ip = "10.110.0.10"
  }

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
    ManagedBy   = "terraform"
  }
}


# ============================================================
# PRODUCTION APPLICATION NODE POOL
#
# Application workloads are isolated from system-critical
# Kubernetes services.
#
# The pool can scale independently according to application
# scheduling pressure.
# ============================================================

resource "azurerm_kubernetes_cluster_node_pool" "prod_user" {
  provider = azurerm.prod

  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.prod.id

  mode    = "User"
  vm_size = "Standard_D2s_v5"

  auto_scaling_enabled = true
  min_count            = 1
  max_count            = 5

  vnet_subnet_id = data.terraform_remote_state.network.outputs.prod_aks_subnet_id

  node_labels = {
    workload = "application"
  }

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
    ManagedBy   = "terraform"
    NodePool    = "user"
  }
}


# ============================================================
# NON-PRODUCTION AKS CLUSTER
#
# NonProduction keeps the same security and architectural
# boundaries as Production while using a more cost-conscious
# capacity model.
# ============================================================

resource "azurerm_kubernetes_cluster" "nonprod" {
  provider = azurerm.nonprod

  name                = "sog-nonprod-aks"
  location            = data.terraform_remote_state.network.outputs.nonprod_spoke_location
  resource_group_name = azurerm_resource_group.nonprod_platform.name
  dns_prefix          = "sog-nonprod-aks"

  private_cluster_enabled = true

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  role_based_access_control_enabled = true

  azure_active_directory_role_based_access_control {
    azure_rbac_enabled = true
    tenant_id          = data.azurerm_client_config.current.tenant_id
  }

  # ----------------------------------------------------------
  # SYSTEM NODE POOL
  #
  # NonProduction keeps at least one system node but can scale
  # to two when cluster/platform demand increases.
  # ----------------------------------------------------------

  default_node_pool {
    name = "system"

    vm_size = "Standard_D2s_v5"

    auto_scaling_enabled = true
    min_count            = 1
    max_count            = 2

    only_critical_addons_enabled = true

    vnet_subnet_id = data.terraform_remote_state.network.outputs.nonprod_aks_subnet_id

    type = "VirtualMachineScaleSets"

    tags = {
      Environment = "nonproduction"
      Owner       = "platform-team"
      CostCenter  = "nonproduction"
      ManagedBy   = "terraform"
      NodePool    = "system"
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "azure"

    outbound_type = "userDefinedRouting"

    service_cidr   = "10.120.0.0/16"
    dns_service_ip = "10.120.0.10"
  }

  tags = {
    Environment = "nonproduction"
    Owner       = "platform-team"
    CostCenter  = "nonproduction"
    ManagedBy   = "terraform"
  }
}


# ============================================================
# NON-PRODUCTION APPLICATION NODE POOL
#
# NonProduction application capacity can scale down to zero
# when there are no schedulable application workloads.
# ============================================================

resource "azurerm_kubernetes_cluster_node_pool" "nonprod_user" {
  provider = azurerm.nonprod

  name                  = "user"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.nonprod.id

  mode    = "User"
  vm_size = "Standard_D2s_v5"

  auto_scaling_enabled = true
  min_count            = 0
  max_count            = 3

  vnet_subnet_id = data.terraform_remote_state.network.outputs.nonprod_aks_subnet_id

  node_labels = {
    workload = "application"
  }

  tags = {
    Environment = "nonproduction"
    Owner       = "platform-team"
    CostCenter  = "nonproduction"
    ManagedBy   = "terraform"
    NodePool    = "user"
  }
}