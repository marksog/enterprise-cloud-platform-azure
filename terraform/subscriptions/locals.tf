locals {
  subscriptions = {
    production = {
      subscription_id     = "/subscriptions/e3bda1e9-e6e9-45a5-b2ee-d3d7a754b594"
      management_group_id = data.terraform_remote_state.management_groups.outputs.production_management_group_id
    }

    nonproduction = {
      subscription_id     = "/subscriptions/4eeb7aa0-684a-473d-9ae3-f238dfc3f944"
      management_group_id = data.terraform_remote_state.management_groups.outputs.nonproduction_management_group_id
    }
  }
}

locals {
  rbac_assignments = {
    platform_admins = {
      principal_id         = "d35f4a8e-12c6-433a-b539-21c7661d3102"
      role_definition_name = "Contributor"
      scope                = "/subscriptions/e3bda1e9-e6e9-45a5-b2ee-d3d7a754b594"
    }

    security_readers = {
      principal_id         = "1815b8e6-63e7-4826-a308-e192240d150c"
      role_definition_name = "Security Reader"
      scope                = "/subscriptions/e3bda1e9-e6e9-45a5-b2ee-d3d7a754b594"
    }

    finops_readers = {
      principal_id         = "c72ef9d7-ae36-46e3-8f53-67bbe2d1966b"
      role_definition_name = "Cost Management Reader"
      scope                = "/subscriptions/e3bda1e9-e6e9-45a5-b2ee-d3d7a754b594"
    }

    payments_prod_contributors = {
      principal_id         = "1c758c52-a1a8-4bdd-a23b-864546ff85f8"
      role_definition_name = "Contributor"
      scope                = "/subscriptions/e3bda1e9-e6e9-45a5-b2ee-d3d7a754b594"
    }
  }
}