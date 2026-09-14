# ============================================================
# SUBSCRIPTION IDs
#
# Identity resources are deployed across the Production and
# Non-Production subscriptions.
# ============================================================

variable "prod_subscription_id" {
  description = "Azure subscription ID for the Production environment."
  type        = string
}

variable "nonprod_subscription_id" {
  description = "Azure subscription ID for the Non-Production environment."
  type        = string
}


variable "workload_identities" {
  description = "Applications that require environment-scoped Azure workload managed identities."

  type = map(object({
    environment = string
    owner       = string
    cost_center = string
  }))

  default = {}

  validation {
    condition = alltrue([
      for name, config in var.workload_identities :
      contains(["production", "nonproduction"], config.environment)
      && can(regex("^[a-z0-9-]+$", name))
    ])

    error_message = "Each workload identity must use environment production or nonproduction, and application names may contain only lowercase letters, numbers, and hyphens."
  }
}