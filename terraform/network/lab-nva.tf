# ============================================================
# LAB NETWORK VIRTUAL APPLIANCE
#
# Cost-conscious replacement for Azure Firewall in this lab.
# NOT equivalent to Azure Firewall in production.
# ============================================================

resource "azurerm_public_ip" "lab_nva" {
  name                = "sog-lab-nva-pip"
  location            = azurerm_virtual_network.hub.location
  resource_group_name = azurerm_resource_group.hub.name

  allocation_method = "Static"
  sku               = "Standard"

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
    Purpose     = "lab-nva"

  }
}

resource "azurerm_network_interface" "lab_nva" {
  name                = "sog-lab-nva-nic"
  location            = azurerm_virtual_network.hub.location
  resource_group_name = azurerm_resource_group.hub.name
  # Critical for an NVA:
  # Azure must permit the NIC to forward packets
  # that are not addressed to the VM itself.
  ip_forwarding_enabled = true

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.hub_nva.id
    private_ip_address_allocation = "Static"
    private_ip_address            = "10.0.0.196"
    public_ip_address_id          = azurerm_public_ip.lab_nva.id
  }

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
    Purpose     = "lab-nva"
  }
}

resource "azurerm_linux_virtual_machine" "lab_nva" {
  name                = "sog-lab-nva"
  resource_group_name = azurerm_resource_group.hub.name
  location            = azurerm_virtual_network.hub.location

  size = "Standard_D2s_v7"

  admin_username                  = "azureadmin"
  disable_password_authentication = true

  network_interface_ids = [
    azurerm_network_interface.lab_nva.id
  ]

  admin_ssh_key {
    username   = "azureadmin"
    public_key = var.nva_admin_ssh_public_key
  }

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts-gen2"
    version   = "latest"
  }

  custom_data = base64encode(<<-CLOUDINIT
    #cloud-config

    write_files:
      - path: /etc/sysctl.d/99-sog-nva.conf
        content: |
          net.ipv4.ip_forward=1

    runcmd:
      - sysctl --system

      # NAT traffic leaving the NVA.
      - iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

      # Permit return traffic for established connections.
      - iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

      # Lab policy:
      # Application and AKS subnets may transit toward the internet.
      - iptables -A FORWARD -s 10.10.0.0/24 -j ACCEPT
      - iptables -A FORWARD -s 10.10.3.0/24 -j ACCEPT
      - iptables -A FORWARD -s 10.20.0.0/24 -j ACCEPT
      - iptables -A FORWARD -s 10.20.3.0/24 -j ACCEPT

      # Data tiers do NOT receive general transit permission.
      - iptables -A FORWARD -s 10.10.1.0/24 -j DROP
      - iptables -A FORWARD -s 10.20.1.0/24 -j DROP

      - iptables -A FORWARD -j DROP
  CLOUDINIT
  )

  tags = {
    Environment = "platform"
    Owner       = "networking-team"
    CostCenter  = "platform"
    Purpose     = "lab-nva"
  }
}