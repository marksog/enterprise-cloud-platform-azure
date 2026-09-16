# ============================================================
# SUBSCRIPTION IDs
#
# Platform resources are deployed into their respective
# Production and Non-Production subscriptions.
# ============================================================

variable "prod_subscription_id" {
  description = "Azure subscription ID for the Production environment."
  type        = string
}

variable "nonprod_subscription_id" {
  description = "Azure subscription ID for the Non-Production environment."
  type        = string
}

# ============================================================
# AKS HUMAN ADMINISTRATION
#
# Microsoft Entra security groups authorized to administer
# the AKS clusters.
#
# Group membership is managed outside this Terraform stack.
# The platform consumes group object IDs rather than assigning
# permissions directly to individual human users.
# ============================================================

variable "nonprod_aks_admin_group_object_ids" {
  description = "Microsoft Entra security group object IDs authorized as AKS RBAC Cluster Admins in Non-Production."
  type        = set(string)
  default     = []
}

variable "prod_aks_admin_group_object_ids" {
  description = "Microsoft Entra security group object IDs authorized as AKS RBAC Cluster Admins in Production."
  type        = set(string)
  default     = []
}