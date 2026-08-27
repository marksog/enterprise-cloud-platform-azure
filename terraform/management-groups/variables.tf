variable "org_prefix" {
  description = "Organization prefix used in management group IDs and naming."
  type        = string
}

variable "organization_name" {
  description = "Human-readable organization name."
  type        = string
}

variable "org_prefix" {
  description = "Organization prefix used to derive standardized management group IDs."
  type        = string
}

variable "organization_hierarchy" {
  description = "Desired management group hierarchy for the organization."

  type = map(object({
    display_name = string
    parent       = optional(string)
  }))

  validation {
    condition = alltrue([
      for key, group in var.organization_hierarchy :
      group.parent == null || contains(keys(var.organization_hierarchy), group.parent)
    ])

    error_message = "Each parent must either be null or reference another key in organization_hierarchy."
  }
}