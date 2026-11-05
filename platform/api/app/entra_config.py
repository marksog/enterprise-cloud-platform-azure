"""
Microsoft Entra ID configuration for SOG Platform API.
"""

import os

TENANT_ID = os.getenv(
    "SOG_ENTRA_TENANT_ID",
    "b854e21e-defb-4268-8398-05ca9757a1af",
)

API_CLIENT_ID = os.getenv(
    "SOG_ENTRA_API_CLIENT_ID",
    "c705d7f9-8c81-4649-88b4-55b530b50353",
)

ISSUER = (
    f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
)

OIDC_DISCOVERY_URL = (
    f"{ISSUER}/.well-known/openid-configuration"
)

REQUIRED_SCOPE = "access_as_user"

COMMERCE_DEVELOPERS_GROUP_ID = os.getenv(
    "SOG_COMMERCE_DEVELOPERS_GROUP_ID",
    "229784ae-e9ff-479d-8ddb-06edd498170a",
)