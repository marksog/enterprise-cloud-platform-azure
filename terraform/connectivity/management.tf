# ============================================================
# PLATFORM MANAGEMENT PLANE
#
# Provides a controlled administrative path to private platform
# resources such as the Prod and NonProd AKS API servers.
#
# Access model:
#
# Administrator
#      |
#      v
# Azure Bastion
#      |
#      v
# Private Management VM
#      |
#      +----> Prod private AKS API
#      |
#      +----> NonProd private AKS API
#
# The management VM has no public IP.
# ============================================================


# ============================================================
# MANAGEMENT NSG
# ============================================================

resource "azurerm_network_security_group" "management" {
  name                = "sog-management-nsg"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
    Purpose     = "privileged-management"
    ManagedBy   = "terraform"
  }
}


# ============================================================
# ALLOW SSH FROM AZURE BASTION
#
# Only resources originating from AzureBastionSubnet may SSH
# to the management VM.
# ============================================================

resource "azurerm_network_security_rule" "management_ssh_from_bastion" {
  name                       = "Allow-SSH-From-Bastion"
  priority                   = 100
  direction                  = "Inbound"
  access                     = "Allow"
  protocol                   = "Tcp"
  source_port_range          = "*"
  destination_port_range     = "22"
  source_address_prefix      = "10.30.0.64/26"
  destination_address_prefix = "10.30.0.224/27"

  resource_group_name         = azurerm_resource_group.hub.name
  network_security_group_name = azurerm_network_security_group.management.name
}


# ============================================================
# MANAGEMENT SUBNET NSG ASSOCIATION
# ============================================================

resource "azurerm_subnet_network_security_group_association" "management" {
  subnet_id                 = azurerm_subnet.hub_management.id
  network_security_group_id = azurerm_network_security_group.management.id
}


# ============================================================
# AZURE BASTION PUBLIC IP
#
# The Bastion service requires its own Standard static
# public IP. The management VM itself remains private.
# ============================================================

resource "azurerm_public_ip" "bastion" {
  name                = "sog-bastion-pip"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name

  allocation_method = "Static"
  sku               = "Standard"

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
    Purpose     = "secure-administration"
    ManagedBy   = "terraform"
  }
}


# ============================================================
# AZURE BASTION
#
# Bastion resides in the reserved AzureBastionSubnet.
#
# Administrators connect to private management hosts through
# Bastion without assigning public IPs to those hosts.
# ============================================================

resource "azurerm_bastion_host" "platform" {
  name                = "sog-platform-bastion"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name

  sku = "Basic"

  ip_configuration {
    name                 = "bastion-ip-config"
    subnet_id            = azurerm_subnet.hub_bastion.id
    public_ip_address_id = azurerm_public_ip.bastion.id
  }

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
    Purpose     = "secure-administration"
    ManagedBy   = "terraform"
  }
}


# ============================================================
# MANAGEMENT VM NIC
#
# No public IP is attached.
# ============================================================

resource "azurerm_network_interface" "management" {
  name                = "sog-platform-admin-nic"
  location            = azurerm_resource_group.hub.location
  resource_group_name = azurerm_resource_group.hub.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.hub_management.id
    private_ip_address_allocation = "Dynamic"
  }

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
    Purpose     = "privileged-management"
    ManagedBy   = "terraform"
  }
}


# ============================================================
# PLATFORM ADMINISTRATION VM
#
# Private operational workstation for platform engineers.
#
# Initial tooling:
#   - Azure CLI
#   - kubectl
#   - kubelogin
#   - Helm
#
# Authentication credentials are NOT embedded in Terraform.
# ============================================================

resource "azurerm_linux_virtual_machine" "management" {
  name                = "sog-platform-admin-vm"
  resource_group_name = azurerm_resource_group.hub.name
  location            = azurerm_resource_group.hub.location

  size = "Standard_D2as_v7"

  admin_username                  = "azureadmin"
  disable_password_authentication = true

  network_interface_ids = [
    azurerm_network_interface.management.id
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

    package_update: true

    packages:
      - curl
      - unzip
      - ca-certificates
      - apt-transport-https
      - gnupg
      - lsb-release

    runcmd:

      # ------------------------------------------------------
      # Azure CLI
      # ------------------------------------------------------
      - curl -sL https://aka.ms/InstallAzureCLIDeb | bash

      # ------------------------------------------------------
      # kubectl
      # ------------------------------------------------------
      - curl -LO "https://dl.k8s.io/release/v1.35.0/bin/linux/amd64/kubectl"
      - install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
      - rm kubectl

      # ------------------------------------------------------
      # kubelogin
      # ------------------------------------------------------
      - curl -L https://github.com/Azure/kubelogin/releases/latest/download/kubelogin-linux-amd64.zip -o /tmp/kubelogin.zip
      - unzip /tmp/kubelogin.zip -d /tmp/kubelogin
      - install -o root -g root -m 0755 /tmp/kubelogin/bin/linux_amd64/kubelogin /usr/local/bin/kubelogin

      # ------------------------------------------------------
      # Helm
      # ------------------------------------------------------
      - curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash

  CLOUDINIT
  )

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
    Purpose     = "privileged-management"
    ManagedBy   = "terraform"
  }
}