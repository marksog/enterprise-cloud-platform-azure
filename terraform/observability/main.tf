resource "azurerm_resource_group" "observability" {
  name     = "sog-platform-observability-rg"
  location = "eastus"

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
  }
}

resource "azurerm_log_analytics_workspace" "central" {
  name                = "sog-central-observability-law"
  location            = azurerm_resource_group.observability.location
  resource_group_name = azurerm_resource_group.observability.name

  sku               = "PerGB2018"
  retention_in_days = 30

  tags = {
    Environment = "platform"
    Owner       = "platform-team"
    CostCenter  = "platform"
  }
}

# Production subscription activity logs
resource "azurerm_monitor_diagnostic_setting" "production_activity_logs" {
  name                       = "prod-activity-logs-to-law"
  target_resource_id         = "/subscriptions/e3bda1e9-e6e9-45a5-b2ee-d3d7a754b594"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.central.id

  provider = azurerm.prod

  enabled_log {
    category = "Administrative"
  }

  enabled_log {
    category = "Security"
  }

  enabled_log {
    category = "ServiceHealth"
  }

  enabled_log {
    category = "Alert"
  }

  enabled_log {
    category = "Recommendation"
  }

  enabled_log {
    category = "Policy"
  }
}

# Non-Production subscription activity logs
resource "azurerm_monitor_diagnostic_setting" "nonproduction_activity_logs" {
  name                       = "nonprod-activity-logs-to-law"
  target_resource_id         = "/subscriptions/4eeb7aa0-684a-473d-9ae3-f238dfc3f944"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.central.id

  provider = azurerm.nonprod

  enabled_log {
    category = "Administrative"
  }

  enabled_log {
    category = "Security"
  }

  enabled_log {
    category = "ServiceHealth"
  }

  enabled_log {
    category = "Alert"
  }

  enabled_log {
    category = "Recommendation"
  }

  enabled_log {
    category = "Policy"
  }
}