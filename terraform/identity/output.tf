# ============================================================
# IDENTITY FOUNDATION OUTPUTS
# ============================================================

output "prod_identity_resource_group_id" {
  description = "Resource ID of the Production identity resource group."
  value       = azurerm_resource_group.prod_identity.id
}

output "nonprod_identity_resource_group_id" {
  description = "Resource ID of the Non-Production identity resource group."
  value       = azurerm_resource_group.nonprod_identity.id
}

output "prod_workload_identities" {
  description = "Production workload identities keyed by application name."

  value = {
    for name, identity in azurerm_user_assigned_identity.prod_workload : name => {
      id           = identity.id
      client_id    = identity.client_id
      principal_id = identity.principal_id
    }
  }
}

output "nonprod_workload_identities" {
  description = "Non-Production workload identities keyed by application name."

  value = {
    for name, identity in azurerm_user_assigned_identity.nonprod_workload : name => {
      id           = identity.id
      client_id    = identity.client_id
      principal_id = identity.principal_id
    }
  }
}