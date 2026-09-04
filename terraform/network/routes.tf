# ============================================================
# PRODUCTION ROUTING
# Force workload egress through the Hub NVA
# ============================================================

resource "azurerm_route_table" "prod" {
  provider = azurerm.prod

  name                = "prod-egress-rt"
  location            = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_location
  resource_group_name = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name

  bgp_route_propagation_enabled = true

  route {
    name                   = "default-via-hub-nva"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = "10.0.0.196"
  }

  tags = {
    Environment = "production"
    Owner       = "networking-team"
    CostCenter  = "production"
  }
}

resource "azurerm_subnet_route_table_association" "prod_app" {
  provider = azurerm.prod

  subnet_id      = azurerm_subnet.prod_app.id
  route_table_id = azurerm_route_table.prod.id
}

resource "azurerm_subnet_route_table_association" "prod_aks" {
  provider = azurerm.prod

  subnet_id      = azurerm_subnet.prod_aks.id
  route_table_id = azurerm_route_table.prod.id
}

resource "azurerm_subnet_route_table_association" "prod_data" {
  provider = azurerm.prod

  subnet_id      = azurerm_subnet.prod_data.id
  route_table_id = azurerm_route_table.prod.id
}


# ============================================================
# NON-PRODUCTION ROUTING
# Force workload egress through the Hub NVA
# ============================================================

resource "azurerm_route_table" "nonprod" {
  provider = azurerm.nonprod

  name                = "nonprod-egress-rt"
  location            = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_location
  resource_group_name = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_name

  bgp_route_propagation_enabled = true

  route {
    name                   = "default-via-hub-nva"
    address_prefix         = "0.0.0.0/0"
    next_hop_type          = "VirtualAppliance"
    next_hop_in_ip_address = "10.0.0.196"
  }

  tags = {
    Environment = "nonproduction"
    Owner       = "networking-team"
    CostCenter  = "nonproduction"
  }
}

resource "azurerm_subnet_route_table_association" "nonprod_app" {
  provider = azurerm.nonprod

  subnet_id      = azurerm_subnet.nonprod_app.id
  route_table_id = azurerm_route_table.nonprod.id
}

resource "azurerm_subnet_route_table_association" "nonprod_aks" {
  provider = azurerm.nonprod

  subnet_id      = azurerm_subnet.nonprod_aks.id
  route_table_id = azurerm_route_table.nonprod.id
}

resource "azurerm_subnet_route_table_association" "nonprod_data" {
  provider = azurerm.nonprod

  subnet_id      = azurerm_subnet.nonprod_data.id
  route_table_id = azurerm_route_table.nonprod.id
}