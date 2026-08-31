variable "management_group_id" {
  description = "Management group where custom policy definitions are created."
  type        = string
}

variable "required_tags" {
  description = "Enterprise tags required on taggable Azure resources."
  type        = set(string)
}