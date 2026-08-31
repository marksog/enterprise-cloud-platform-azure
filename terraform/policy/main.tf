
data "terraform_remote_state" "management_groups" {
  backend = "azurerm"

  config = {
    resource_group_name  = "sog-platform-bootstrap-rg"
    storage_account_name = "sogtfstate001"
    container_name       = "tfstate"
    key                  = "management-groups.tfstate"

    use_oidc         = true
    use_azuread_auth = true
  }
}



module "built_ins" {
  source = "./modules/built-ins"
}

module "definitions" {
  source = "./modules/definitions"

  management_group_id = data.terraform_remote_state.management_groups.outputs.enterprise_management_group_id
  required_tags       = local.required_tags
}

module "initiatives" {
  source = "./modules/initiatives"

  management_group_id        = data.terraform_remote_state.management_groups.outputs.enterprise_management_group_id
  storage_public_access_id   = module.built_ins.storage_public_access_id
  storage_secure_transfer_id = module.built_ins.storage_secure_transfer_id
  storage_minimum_tls_id     = module.built_ins.storage_minimum_tls_id
  allowed_locations_id       = module.built_ins.allowed_locations_id
  required_tags_id           = module.definitions.required_tags_id
}

module "assignments" {
  source = "./modules/assignments"

  enterprise_management_group_id  = data.terraform_remote_state.management_groups.outputs.enterprise_management_group_id
  enterprise_security_baseline_id = module.initiatives.enterprise_security_baseline_id
  allowed_locations               = local.allowed_locations
}