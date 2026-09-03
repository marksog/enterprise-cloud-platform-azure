locals {
  required_tags = [
    "Environment",
    "Owner",
    "CostCenter"
  ]

  allowed_locations = [
    "eastus",
    "eastus2",
    "westus3"
  ]
}