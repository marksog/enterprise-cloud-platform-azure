"""
SOG Platform API — JWKS Rotation and Failure Tests.

Tests signing-key caching, key rotation, and failure handling
without contacting Microsoft Entra ID.
"""

import json
from datetime import datetime, timedelta, timezone

import jwt
import pytest

from cryptography.hazmat.primitives.asymmetric import rsa
from jwt import PyJWKClient

from app import auth
from app.entra_config import (
    API_CLIENT_ID,
    ISSUER,
    REQUIRED_SCOPE,
    TENANT_ID,
)


def generate_key(kid):
    """Generate an RSA key and corresponding public JWK."""

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key = private_key.public_key()

    jwk = json.loads(
        jwt.algorithms.RSAAlgorithm.to_jwk(public_key)
    )

    jwk["kid"] = kid
    jwk["use"] = "sig"
    jwk["alg"] = "RS256"

    return private_key, jwk


def make_token(private_key, kid):
    """Create a signed test access token."""

    now = datetime.now(timezone.utc)

    claims = {
        "iss": ISSUER,
        "aud": API_CLIENT_ID,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=30),
        "tid": TENANT_ID,
        "oid": "test-developer-id",
        "scp": REQUIRED_SCOPE,
        "groups": ["test-commerce-group"],
    }

    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": kid},
    )


def test_jwks_key_rotation(monkeypatch):
    """
    Unknown kid should trigger JWKS refresh.
    """

    old_private_key, old_jwk = generate_key("old-key")
    new_private_key, new_jwk = generate_key("new-key")

    responses = [
        {"keys": [old_jwk]},
        {"keys": [old_jwk, new_jwk]},
    ]

    class MockJWKSClient(PyJWKClient):

        def __init__(self):
            super().__init__(
                "https://example.invalid/jwks",
                lifespan=300,
            )
            self.fetch_count = 0

        def fetch_data(self):
            index = min(
                self.fetch_count,
                len(responses) - 1,
            )

            self.fetch_count += 1

            data = responses[index]

            if self.jwk_set_cache is not None:
                self.jwk_set_cache.put(data)

            return data

    client = MockJWKSClient()

    monkeypatch.setattr(
        auth,
        "get_jwks_client",
        lambda: client,
    )

    old_token = make_token(
        old_private_key,
        "old-key",
    )

    new_token = make_token(
        new_private_key,
        "new-key",
    )

    old_identity = auth.verify_access_token(old_token)
    new_identity = auth.verify_access_token(new_token)

    assert old_identity.user_id == "test-developer-id"
    assert new_identity.user_id == "test-developer-id"

    assert client.fetch_count == 2


def test_jwks_outage_fails_closed(monkeypatch):
    """
    JWKS unavailability must never permit
    an unverified token.
    """

    private_key, _ = generate_key("unknown-key")

    class UnavailableJWKSClient:

        def get_signing_key_from_jwt(self, token):
            raise OSError(
                "JWKS endpoint unavailable"
            )

    monkeypatch.setattr(
        auth,
        "get_jwks_client",
        lambda: UnavailableJWKSClient(),
    )

    token = make_token(
        private_key,
        "unknown-key",
    )

    with pytest.raises(
        auth.AuthenticationServiceUnavailable
    ):
        auth.verify_access_token(token)


def test_cached_key_remains_usable(monkeypatch):
    """
    A previously cached key should remain usable
    when JWKS retrieval is unavailable.
    """

    private_key, public_jwk = generate_key("cached-key")

    class CachedJWKSClient(PyJWKClient):

        def __init__(self):
            super().__init__(
                "https://example.invalid/jwks",
                lifespan=300,
            )

            self.fetch_count = 0

            self.jwk_set_cache.put({
                "keys": [public_jwk]
            })

        def fetch_data(self):
            self.fetch_count += 1
            raise OSError(
                "JWKS endpoint unavailable"
            )

    client = CachedJWKSClient()

    monkeypatch.setattr(
        auth,
        "get_jwks_client",
        lambda: client,
    )

    token = make_token(
        private_key,
        "cached-key",
    )

    identity = auth.verify_access_token(token)

    assert identity.user_id == "test-developer-id"

    # Cached key means no network request was needed.
    assert client.fetch_count == 0