# ============================================================
# WORKLOAD MODULE INPUT CONTRACT
#
# Application teams express workload intent through this
# interface. Platform implementation details remain internal
# to the module.
# ============================================================


# ------------------------------------------------------------
# WORKLOAD IDENTITY
# ------------------------------------------------------------

variable "name" {
  description = "Logical application name used by the platform to derive workload resource names."
  type        = string

  validation {
    condition = (
      length(var.name) >= 3 &&
      length(var.name) <= 40 &&
      can(regex("^[a-z0-9]+(?:-[a-z0-9]+)*$", var.name))
    )

    error_message = "Workload name must be 3-40 characters and contain only lowercase letters, numbers, and single hyphens between words."
  }
}


# ------------------------------------------------------------
# APPLICATION IMAGE
# ------------------------------------------------------------

variable "image" {
  description = "Container image and tag to deploy for the workload."
  type        = string

  validation {
    condition     = length(trimspace(var.image)) > 0
    error_message = "Workload image must not be empty."
  }
}


# ------------------------------------------------------------
# APPLICATION PORT
# ------------------------------------------------------------

variable "port" {
  description = "TCP port on which the application listens."
  type        = number

  validation {
    condition     = var.port >= 1 && var.port <= 65535
    error_message = "Workload port must be between 1 and 65535."
  }
}


# ------------------------------------------------------------
# CAPACITY PROFILE
# ------------------------------------------------------------

variable "size" {
  description = "Platform-defined workload capacity profile."
  type        = string
  default     = "small"

  validation {
    condition = contains(
      ["small", "medium", "large"],
      var.size
    )

    error_message = "Workload size must be one of: small, medium, large."
  }
}


# ------------------------------------------------------------
# EXPOSURE PROFILE
# ------------------------------------------------------------

variable "exposure" {
  description = "Platform-defined workload network exposure profile."
  type        = string
  default     = "internal"

  validation {
    condition = contains(
      ["none", "internal", "public"],
      var.exposure
    )

    error_message = "Workload exposure must be one of: none, internal, public."
  }
}


# ------------------------------------------------------------
# AZURE CAPABILITY REQUESTS
# ------------------------------------------------------------

variable "domain_key_vault_id" {
  description = "Resource ID of the Key Vault assigned to the workload's domain. Null when the domain has no secret store."
  type        = string
  default     = null
  nullable    = true
}

variable "environment" {
  description = "Platform environment in which the workload is deployed."
  type        = string

  validation {
    condition     = contains(["nonprod", "prod"], var.environment)
    error_message = "Environment must be one of: nonprod, prod."
  }
}

variable "namespace_name" {
  description = "Kubernetes namespace assigned to the workload by the environment domain layer."
  type        = string

  validation {
    condition     = length(trimspace(var.namespace_name)) > 0
    error_message = "Workload namespace_name must not be empty."
  }
}

# ------------------------------------------------------------
# PLATFORM-PROVIDED AZURE CONTEXT
# ------------------------------------------------------------

variable "azure_resource_group_name" {
  description = "Azure resource group in which workload-specific Azure resources are created."
  type        = string
}

variable "azure_location" {
  description = "Azure region for workload-specific Azure resources."
  type        = string
}

variable "aks_oidc_issuer_url" {
  description = "OIDC issuer URL of the AKS cluster used for Workload Identity federation."
  type        = string
}

variable "domain_secret_store_enabled" {
  description = "Whether the workload's domain provides a secret store capability."
  type        = bool
  default     = false
}