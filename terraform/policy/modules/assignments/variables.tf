variable "enterprise_management_group_id" {
  description = "Resource ID of the Enterprise management group."
  type        = string
}

variable "enterprise_security_baseline_id" {
  description = "Resource ID of the Enterprise Security Baseline initiative."
  type        = string
}

variable "allowed_locations" {
  description = "Azure regions approved for enterprise workloads."
  type        = list(string)
}