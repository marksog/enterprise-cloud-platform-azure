# ============================================================
# AZURE FIREWALL - PRODUCTION REFERENCE ARCHITECTURE
#
# NOT DEPLOYED IN THIS LAB DUE TO COST.
#
# In production, the Linux NVA used by this lab would be
# replaced by a managed Azure Firewall deployment.
# ============================================================


# resource "azurerm_public_ip" "firewall" {
#   name                = "sog-azure-firewall-pip"
#   location            = azurerm_resource_group.hub.location
#   resource_group_name = azurerm_resource_group.hub.name
#
#   allocation_method = "Static"
#   sku               = "Standard"
# }


# resource "azurerm_firewall_policy" "central" {
#   name                = "sog-central-firewall-policy"
#   location            = azurerm_resource_group.hub.location
#   resource_group_name = azurerm_resource_group.hub.name
#
#   sku = "Standard"
# }


# resource "azurerm_firewall" "central" {
#   name                = "sog-central-firewall"
#   location            = azurerm_resource_group.hub.location
#   resource_group_name = azurerm_resource_group.hub.name
#
#   sku_name = "AZFW_VNet"
#   sku_tier = "Standard"
#
#   firewall_policy_id = azurerm_firewall_policy.central.id
#
#   ip_configuration {
#     name                 = "configuration"
#     subnet_id            = azurerm_subnet.hub_firewall.id
#     public_ip_address_id = azurerm_public_ip.firewall.id
#   }
# }


# In the production implementation, spoke UDRs would point to
# the Azure Firewall's PRIVATE IP instead of the lab NVA:
#
# address_prefix         = "0.0.0.0/0"
# next_hop_type          = "VirtualAppliance"
# next_hop_in_ip_address = azurerm_firewall.central.ip_configuration[0].private_ip_address
#
#
# Traffic path:
#
# Prod / NonProd workload
#          |
#          | UDR
#          v
# Azure Firewall
#          |
#          +--> Network rules
#          +--> Application rules
#          +--> DNAT/SNAT
#          +--> Threat intelligence
#          +--> Central logging
#          |
#          v
# Internet / permitted destination