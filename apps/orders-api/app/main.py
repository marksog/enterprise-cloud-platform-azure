import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import FastAPI, HTTPException
import time

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI(
    title="Orders API",
    version="1.0.0",
)

REQUEST_COUNT = Counter(
    "orders_api_http_requests_total",
    "Total number of HTTP requests handled by orders-api",
    ["method", "path", "status_code"],
)

REQUEST_DURATION = Histogram(
    "orders_api_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)

KEY_VAULT_URL = os.getenv(
    "KEY_VAULT_URL",
    "https://sog-nonprod-commerce-kv.vault.azure.net",
)


@app.middleware("http")
async def observe_requests(request, call_next):
    start_time = time.perf_counter()

    response = await call_next(request)

    if request.url.path != "/metrics":
        duration = time.perf_counter() - start_time

        REQUEST_COUNT.labels(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method,
            path=request.url.path,
        ).observe(duration)

    return response


@app.get("/")
def root():
    return {
        "service": "orders-api",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/identity-test")
def identity_test():
    """
    Proves the complete AKS Workload Identity -> Azure Key Vault path.
    """
    try:
        credential = DefaultAzureCredential()
        client = SecretClient(
            vault_url=KEY_VAULT_URL,
            credential=credential,
        )

        secret = client.get_secret("orders-api-test")

        return {
            "status": "success",
            "key_vault_access": bool(secret.value),
            "secret_name": secret.name,
        }

    except Exception:
        raise HTTPException(
            status_code=500,
            detail="Key Vault access failed",
        )