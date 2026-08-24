variable "org_prefix" {
  description = "Organization prefix used to derive standardized resource names."
  type        = string
}

variable "location" {
  description = "Azure region where bootstrap resources will be deployed."
  type        = string
}

variable "unique_suffix" {
  description = "Unique suffix used to ensure globally unique resource names where required."
  type        = string
}

variable "account_tier" {
  description = "Storage account tier. Valid values: Standard, Premium."
  type        = string
  default     = "Standard"

  validation {
    condition     = contains(["Standard", "Premium"], var.account_tier)
    error_message = "account_tier must be either Standard or Premium."
  }
}

variable "account_replication_type" {
  description = "Storage account replication type. Valid values: LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS."
  type        = string
  default     = "LRS"

  validation {
    condition = contains(
      ["LRS", "GRS", "RAGRS", "ZRS", "GZRS", "RAGZRS"],
      var.account_replication_type
    )
    error_message = "account_replication_type must be one of LRS, GRS, RAGRS, ZRS, GZRS, RAGZRS."
  }
}

variable "https_traffic_only_enabled" {
  description = "Whether to enforce HTTPS-only traffic on the storage account."
  type        = bool
  default     = true
}

variable "bootstrap_allowed_ip" {
  description = "Public IPv4 address allowed to access the Terraform state backend during bootstrap."
  type        = string
}