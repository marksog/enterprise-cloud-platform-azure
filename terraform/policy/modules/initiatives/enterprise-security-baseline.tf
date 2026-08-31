resource "azurerm_management_group_policy_set_definition" "enterprise_security_baseline" {
  name                = "enterprise-security-baseline"
  policy_type         = "Custom"
  display_name        = "Enterprise Security Baseline"
  description         = "Enterprise-wide baseline security and governance controls."
  management_group_id = var.management_group_id

  parameters = jsonencode({
    allowedLocations = {
      type = "Array"

      metadata = {
        displayName = "Allowed Azure locations"
        description = "Azure regions approved for enterprise workloads."
        strongType  = "location"
      }
    }
  })

  policy_definition_reference {
    policy_definition_id = var.storage_public_access_id
    reference_id         = "storagePublicAccess"

    parameter_values = jsonencode({
      effect = {
        value = "Deny"
      }
    })
  }

  policy_definition_reference {
    policy_definition_id = var.storage_secure_transfer_id
    reference_id         = "storageSecureTransfer"

    parameter_values = jsonencode({
      effect = {
        value = "Deny"
      }
    })
  }

  policy_definition_reference {
    policy_definition_id = var.storage_minimum_tls_id
    reference_id         = "storageMinimumTls"

    parameter_values = jsonencode({
      effect = {
        value = "Deny"
      }

      minimumTlsVersion = {
        value = "TLS1_2"
      }
    })
  }

  policy_definition_reference {
    policy_definition_id = var.allowed_locations_id
    reference_id         = "allowedLocations"

    parameter_values = jsonencode({
      effect = {
        value = "Deny"
      }

      listOfAllowedLocations = {
        value = "[parameters('allowedLocations')]"
      }
    })
  }

  policy_definition_reference {
    policy_definition_id = var.required_tags_id
    reference_id         = "requiredTags"
  }
}