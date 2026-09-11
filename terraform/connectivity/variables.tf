variable "nva_admin_ssh_public_key" {
  description = "SSH public key used for the lab NVA administrator."
  type        = string
  sensitive   = true
}

variable "nva_admin_source_cidr" {
  description = "Public CIDR permitted to SSH to the lab NVA."
  type        = string
}