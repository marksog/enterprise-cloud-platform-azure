# ============================================================
# NON-PRODUCTION WORKLOAD CATALOG
#
# Application teams declare workload intent here.
# Platform implementation details are handled by the reusable
# workload module.
# ============================================================

variable "workloads" {
  description = "Application workloads deployed to the Non-Production platform."

  type = map(object({
    domain   = string
    image    = string
    port     = number
    size     = optional(string, "small")
    exposure = optional(string, "internal")
  }))

  default = {}
}

variable "domains" {
  description = "Application domains provisioned in the Non-Production environment."

  type = map(object({
    description          = optional(string)
    secret_store_enabled = optional(bool, true)
  }))

  default = {}

  validation {
    condition = alltrue([
      for workload in values(var.workloads) :
      contains(keys(var.domains), workload.domain)
    ])

    error_message = "Every workload domain must reference a domain declared in var.domains."
  }
}

variable "nonprod_subscription_id" {
  description = "Azure subscription ID for the Non-Production workload environment."
  type        = string
}



