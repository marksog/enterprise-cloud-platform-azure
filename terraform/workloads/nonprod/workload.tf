# ============================================================
# NON-PRODUCTION WORKLOADS
#
# Each workload declaration is instantiated through the
# reusable platform workload module.
# ============================================================

module "workload" {
  for_each = var.workloads

  source = "../../modules/workload"

  # Developer workload intent
  name                        = each.key
  image                       = each.value.image
  port                        = each.value.port
  size                        = each.value.size
  exposure                    = each.value.exposure
  domain_key_vault_id         = module.domain[each.value.domain].key_vault_id
  domain_secret_store_enabled = var.domains[each.value.domain].secret_store_enabled

  # Environment/domain context
  environment    = "nonprod"
  namespace_name = module.domain[each.value.domain].namespace_name

  # Platform-provided Azure context
  azure_resource_group_name = data.terraform_remote_state.platform.outputs.nonprod_aks_resource_group_name
  azure_location            = data.terraform_remote_state.platform.outputs.nonprod_aks_location
  aks_oidc_issuer_url       = data.terraform_remote_state.platform.outputs.nonprod_aks_oidc_issuer_url

  # Domain ownership context
  domain_name = each.value.domain
  owner       = var.domains[each.value.domain].owner
  cost_center = var.domains[each.value.domain].cost_center

}

