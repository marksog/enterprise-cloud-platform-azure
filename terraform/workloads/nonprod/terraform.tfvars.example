domains = {
  commerce = {
    description          = "Commerce application workloads"
    secret_store_enabled = true
  }
}

workloads = {
  "orders-api" = {
    domain = "commerce"

    image = "sogplatformacr.azurecr.io/orders-api:v1"
    port  = 8080

    size     = "small"
    exposure = "internal"
  }
}