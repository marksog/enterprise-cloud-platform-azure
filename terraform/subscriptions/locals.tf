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