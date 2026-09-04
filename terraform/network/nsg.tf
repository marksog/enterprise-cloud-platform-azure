# ============================================================
# PRODUCTION DATA NSG
# Protects prod-data-subnet
# ============================================================

resource "azurerm_network_security_group" "prod_data" {
  provider = azurerm.prod

  name                = "prod-data-nsg"
  location            = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_location
  resource_group_name = data.terraform_remote_state.subscriptions.outputs.prod_network_resource_group_name

  security_rule {
    name                       = "allow-app-to-postgres"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5432"
    source_address_prefix      = "10.10.0.0/24"
    destination_address_prefix = "10.10.1.0/24"
  }

  tags = {
    Environment = "production"
    Owner       = "networking-team"
    CostCenter  = "production"
  }
}

resource "azurerm_subnet_network_security_group_association" "prod_data" {
  provider = azurerm.prod

  subnet_id                 = azurerm_subnet.prod_data.id
  network_security_group_id = azurerm_network_security_group.prod_data.id
}

# ============================================================
# NON-PRODUCTION DATA NSG
# Protects nonprod-data-subnet
# ============================================================

resource "azurerm_network_security_group" "nonprod_data" {
  provider = azurerm.nonprod

  name                = "nonprod-data-nsg"
  location            = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_location
  resource_group_name = data.terraform_remote_state.subscriptions.outputs.nonprod_network_resource_group_name

  security_rule {
    name                       = "allow-app-to-postgres"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5432"
    source_address_prefix      = "10.20.0.0/24"
    destination_address_prefix = "10.20.1.0/24"
  }

  security_rule {
    name                       = "allow-aks-to-postgres"
    priority                   = 110
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "5432"
    source_address_prefix      = "10.20.3.0/24"
    destination_address_prefix = "10.20.1.0/24"
  }

  tags = {
    Environment = "nonproduction"
    Owner       = "networking-team"
    CostCenter  = "nonproduction"
  }
}

resource "azurerm_subnet_network_security_group_association" "nonprod_data" {
  provider = azurerm.nonprod

  subnet_id                 = azurerm_subnet.nonprod_data.id
  network_security_group_id = azurerm_network_security_group.nonprod_data.id
}