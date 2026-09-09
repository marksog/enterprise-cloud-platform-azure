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