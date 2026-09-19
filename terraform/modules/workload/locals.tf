# ============================================================
# PLATFORM WORKLOAD PROFILES
#
# These values translate developer-facing workload intent
# into platform-approved Kubernetes runtime configuration.
# ============================================================

locals {
  size_profiles = {
    small = {
      cpu_request    = "100m"
      cpu_limit      = "500m"
      memory_request = "128Mi"
      memory_limit   = "512Mi"

      min_replicas = 1
      max_replicas = 3
    }

    medium = {
      cpu_request    = "250m"
      cpu_limit      = "1000m"
      memory_request = "256Mi"
      memory_limit   = "1Gi"

      min_replicas = 2
      max_replicas = 5
    }

    large = {
      cpu_request    = "500m"
      cpu_limit      = "2000m"
      memory_request = "512Mi"
      memory_limit   = "2Gi"

      min_replicas = 2
      max_replicas = 10
    }
  }

  workload_profile = local.size_profiles[var.size]
  # ----------------------------------------------------------
  # PLATFORM NAMING
  # ----------------------------------------------------------

  resource_prefix = "sog-${var.environment}-${var.name}"



  service_name = var.name

  service_account_name = var.name

  managed_identity_name = "${local.resource_prefix}-identity"

  common_labels = {
    "app.kubernetes.io/name"       = var.name
    "app.kubernetes.io/managed-by" = "sog-platform"
    "sog.io/environment"           = var.environment
  }
}

