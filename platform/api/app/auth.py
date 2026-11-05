"""
SOG Platform API — Microsoft Entra JWT Authentication.

Validates delegated access tokens issued by Microsoft Entra ID.
"""

from dataclasses import dataclass
from functools import lru_cache
import threading
import time
import ssl
import certifi

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientError

from app.entra_config import (
    API_CLIENT_ID,
    ISSUER,
    REQUIRED_SCOPE,
    TENANT_ID,
)

security = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class DeveloperIdentity:
    user_id: str
    groups: tuple[str, ...]


class AuthenticationError(Exception):
    """Raised when access-token validation fails."""


class AuthenticationServiceUnavailable(Exception):
    """Raised when signing keys cannot be retrieved."""

class ControlledJWKSClient(PyJWKClient):
    """
    JWKS client with process-local refresh coordination.

    Limits repeated JWKS refresh attempts caused by
    unknown signing-key IDs.
    """

    def __init__(
        self,
        uri: str,
        refresh_cooldown: float = 30.0,
        **kwargs,
    ):
        super().__init__(uri, **kwargs)

        self._refresh_lock = threading.RLock()
        self._refresh_cooldown = refresh_cooldown
        self._last_refresh_attempt = 0.0

    def get_signing_key(self, kid: str):
        with self._refresh_lock:
            return super().get_signing_key(kid)

    def fetch_data(self):
        with self._refresh_lock:
            now = time.monotonic()

            if (
                self._last_refresh_attempt > 0
                and now - self._last_refresh_attempt
                < self._refresh_cooldown
            ):
                cached = (
                    self.jwk_set_cache.get()
                    if self.jwk_set_cache
                    else None
                )

                if cached is not None:
                    return cached

                raise PyJWKClientError(
                    "JWKS refresh temporarily throttled"
                )

            self._last_refresh_attempt = now

            return super().fetch_data()

@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient:
    """
    Create a reusable JWKS client.

    PyJWKClient caches the JWKS response and can refresh
    signing keys when it encounters an unknown key ID.
    """
    jwks_uri = (
        f"https://login.microsoftonline.com/"
        f"{TENANT_ID}/discovery/v2.0/keys"
    )

    return ControlledJWKSClient(
        jwks_uri,
        cache_jwk_set=True,
        lifespan=300,
        timeout=5,
        refresh_cooldown=30.0,
        ssl_context=ssl.create_default_context(
            cafile=certifi.where()
        ),
    )


def verify_access_token(token: str) -> DeveloperIdentity:
    """Verify a Microsoft Entra access token."""

    try:
        signing_key = get_jwks_client().get_signing_key_from_jwt(
            token
        )

    except jwt.DecodeError as exc:
        raise AuthenticationError(
            "Malformed access token"
        ) from exc

    except PyJWKClientError as exc:
        raise AuthenticationError(
            "Unable to validate token signing key"
        ) from exc

    except (OSError, TimeoutError) as exc:
        raise AuthenticationServiceUnavailable(
            "Identity provider unavailable"
        ) from exc

    try:
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=ISSUER,
            audience=API_CLIENT_ID,
            options={
                "require": [
                    "exp",
                    "iat",
                    "iss",
                    "aud",
                    "tid",
                    "oid",
                    "scp",
                ]
            },
            leeway=30,
        )

    except jwt.PyJWTError as exc:
        raise AuthenticationError(
            "Invalid or expired access token"
        ) from exc

    if payload.get("tid") != TENANT_ID:
        raise AuthenticationError(
            "Unexpected tenant"
        )

    user_id = payload.get("oid")

    if not isinstance(user_id, str) or not user_id:
        raise AuthenticationError(
            "Missing developer identity"
        )

    scopes = payload.get("scp")

    if (
        not isinstance(scopes, str)
        or REQUIRED_SCOPE not in scopes.split()
    ):
        raise AuthenticationError(
            "Required delegated scope missing"
        )

    claim_names = payload.get("_claim_names", {})

    if (
        not isinstance(claim_names, dict)
        or "groups" in claim_names
        or payload.get("hasgroups")
    ):
        raise AuthenticationError(
            "Group membership cannot be verified"
        )

    groups = payload.get("groups", [])

    if (
        not isinstance(groups, list)
        or not all(isinstance(group, str) for group in groups)
    ):
        raise AuthenticationError(
            "Invalid group claims"
        )

    return DeveloperIdentity(
        user_id=user_id,
        groups=tuple(groups),
    )


def get_current_developer(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        security
    ),
) -> DeveloperIdentity:
    """FastAPI dependency for authenticated developers."""

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        return verify_access_token(
            credentials.credentials
        )

    except AuthenticationError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    except AuthenticationServiceUnavailable as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc