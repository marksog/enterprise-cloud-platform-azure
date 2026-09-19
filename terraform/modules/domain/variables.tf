variable "name" {
  description = "Logical application domain or team boundary."
  type        = string

  validation {
    condition = (
      length(var.name) >= 3 &&
      length(var.name) <= 30 &&
      can(regex("^[a-z0-9]+(?:-[a-z0-9]+)*$", var.name))
    )

    error_message = "Domain name must be 3-30 characters and contain only lowercase letters, numbers, and single hyphens."
  }
}

variable "environment" {
  description = "Platform environment containing the domain."
  type        = string

  validation {
    condition     = contains(["nonprod", "prod"], var.environment)
    error_message = "Environment must be one of: nonprod, prod."
  }
}

variable "secret_store_enabled" {
  description = "Whether this domain receives a dedicated Azure Key Vault."
  type        = bool
  default     = true
}

variable "azure_location" {
  description = "Azure region for domain-owned Azure resources."
  type        = string
}

variable "azure_resource_group_name" {
  description = "Resource group for domain-owned Azure resources."
  type        = string
}

variable "tenant_id" {
  description = "Microsoft Entra tenant ID used by the domain Key Vault."
  type        = string
}

variable "private_endpoint_subnet_id" {
  description = "Approved subnet in which domain Private Endpoints are created."
  type        = string
}

variable "key_vault_private_dns_zone_id" {
  description = "Private DNS zone resource ID used by Key Vault Private Link."
  type        = string
}