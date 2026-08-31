variable "management_group_id" {
  description = "Management group where the initiative definition will be created."
  type        = string
}

variable "storage_public_access_id" {
  type = string
}

variable "storage_secure_transfer_id" {
  type = string
}

variable "storage_minimum_tls_id" {
  type = string
}

variable "allowed_locations_id" {
  type = string
}

variable "required_tags_id" {
  type = string
}