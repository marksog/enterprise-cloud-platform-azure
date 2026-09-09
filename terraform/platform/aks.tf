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
  }
}


# ============================================================
# PRODUCTION AKS
# ============================================================

resource "azurerm_kubernetes_cluster" "prod" {
  provider = azurerm.prod

  name                = "sog-prod-aks"
  location            = azurerm_resource_group.prod_platform.location
  resource_group_name = azurerm_resource_group.prod_platform.name
  dns_prefix          = "sog-prod-aks"

  private_cluster_enabled = true

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  role_based_access_control_enabled = true

  default_node_pool {
    name = "system"

    vm_size    = "Standard_B2s"
    node_count = 1

    vnet_subnet_id = data.terraform_remote_state.network.outputs.prod_aks_subnet_id

    type = "VirtualMachineScaleSets"
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "azure"
    outbound_type  = "userDefinedRouting"

    service_cidr   = "10.110.0.0/16"
    dns_service_ip = "10.110.0.10"
  }

  tags = {
    Environment = "production"
    Owner       = "platform-team"
    CostCenter  = "production"
  }
}


# ============================================================
# NON-PRODUCTION AKS
# ============================================================

resource "azurerm_kubernetes_cluster" "nonprod" {
  provider = azurerm.nonprod

  name                = "sog-nonprod-aks"
  location            = azurerm_resource_group.nonprod_platform.location
  resource_group_name = azurerm_resource_group.nonprod_platform.name
  dns_prefix          = "sog-nonprod-aks"

  private_cluster_enabled = true

  oidc_issuer_enabled       = true
  workload_identity_enabled = true

  role_based_access_control_enabled = true

  default_node_pool {
    name = "system"

    vm_size    = "Standard_B2s"
    node_count = 1

    vnet_subnet_id = data.terraform_remote_state.network.outputs.nonprod_aks_subnet_id

    type = "VirtualMachineScaleSets"
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin = "azure"
    network_policy = "azure"
    outbound_type  = "userDefinedRouting"

    service_cidr   = "10.120.0.0/16"
    dns_service_ip = "10.120.0.10"
  }

  tags = {
    Environment = "nonproduction"
    Owner       = "platform-team"
    CostCenter  = "nonproduction"
  }
}