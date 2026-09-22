import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Orders API",
    version="1.0.0",
)

KEY_VAULT_URL = os.getenv(
    "KEY_VAULT_URL",
    "https://sog-nonprod-commerce-kv.vault.azure.net",
)


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