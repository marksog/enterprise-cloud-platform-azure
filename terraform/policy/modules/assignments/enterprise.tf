resource "azurerm_management_group_policy_assignment" "enterprise_security_baseline" {
  name                 = "ent-sec-baseline"
  display_name         = "Enterprise Security Baseline"
  description          = "Applies enterprise-wide security and governance controls."
  management_group_id  = var.enterprise_management_group_id
  policy_definition_id = var.enterprise_security_baseline_id

  parameters = jsonencode({
    allowedLocations = {
      value = var.allowed_locations
    }
  })
}