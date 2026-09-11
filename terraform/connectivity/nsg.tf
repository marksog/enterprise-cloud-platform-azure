resource "azurerm_network_security_group" "nva" {
  name                = "sog-nva-nsg"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
  }
}

resource "azurerm_network_security_rule" "nva_ssh_admin" {
  name                       = "Allow-SSH-Admin"
  priority                   = 100
  direction                  = "Inbound"
  access                     = "Allow"
  protocol                   = "Tcp"
  source_port_range          = "*"
  destination_port_range     = "22"
  source_address_prefix      = var.nva_admin_source_cidr
  destination_address_prefix = "*"

  resource_group_name         = azurerm_resource_group.hub.name
  network_security_group_name = azurerm_network_security_group.nva.name
}

resource "azurerm_subnet_network_security_group_association" "nva" {
  subnet_id                 = azurerm_subnet.hub_nva.id
  network_security_group_id = azurerm_network_security_group.nva.id
}