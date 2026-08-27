locals {
  management_groups = {
    for key, group in var.organization_hierarchy :
    key => {
      name         = lower("${var.org_prefix}-${key}")
      display_name = group.display_name
      parent       = group.parent
    }
  }
}