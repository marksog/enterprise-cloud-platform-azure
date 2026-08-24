locals {
  resource_group_name  = "${var.org_prefix}-platform-bootstrap-rg"
  storage_account_name = lower("${var.org_prefix}tfstate${var.unique_suffix}")
  container_name       = "tfstate"

  common_tags = {
    managed_by = "terraform"
    workload   = "platform"
    purpose    = "terraform-bootstrap"
    owner      = "platform-engineering"
    used_by    = "platform-engineering"
  }
}