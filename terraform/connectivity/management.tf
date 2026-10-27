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
# MANAGEMENT SUBNET NSG ASSOCIATION
# ============================================================

resource "azurerm_subnet_network_security_group_association" "management" {
  subnet_id                 = azurerm_subnet.hub_management.id
  network_security_group_id = azurerm_network_security_group.management.id
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