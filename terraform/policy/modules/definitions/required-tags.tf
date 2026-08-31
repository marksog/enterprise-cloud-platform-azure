resource "azurerm_policy_definition" "required_tags" {
  name                = "required-tags"
  policy_type         = "Custom"
  mode                = "Indexed"
  display_name        = "Require enterprise tags"
  description         = "Requires enterprise-standard tags on taggable Azure resources."
  management_group_id = var.management_group_id

  policy_rule = jsonencode({
    if = {
      anyOf = [
        for tag_name in var.required_tags : {
          field  = "tags[${tag_name}]"
          exists = "false"
        }
      ]
    }

    then = {
      effect = "deny"
    }
  })
}