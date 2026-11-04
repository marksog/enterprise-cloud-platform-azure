"""
SOG Platform API — Authentication Security Tests.
"""

import pytest

from app.auth import (
    AuthenticationError,
    get_current_developer,
    verify_access_token,
)

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import jwt

from cryptography.hazmat.primitives.asymmetric import rsa

from app import auth
from app.entra_config import (
    API_CLIENT_ID,
    ISSUER,
    REQUIRED_SCOPE,
    TENANT_ID,
)


@pytest.fixture
def signing_key(monkeypatch):
    """
    Generate an RSA key for isolated JWT tests.

    Replace the external JWKS lookup with our test key.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    public_key = private_key.public_key()

    class MockJWKSClient:
        def get_signing_key_from_jwt(self, token):
            return SimpleNamespace(key=public_key)

    monkeypatch.setattr(
        auth,
        "get_jwks_client",
        lambda: MockJWKSClient(),
    )

    return private_key


def make_token(private_key, **overrides):
    """Create a signed JWT with configurable claims."""

    now = datetime.now(timezone.utc)

    claims = {
        "iss": ISSUER,
        "aud": API_CLIENT_ID,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=30),
        "tid": TENANT_ID,
        "oid": "test-developer-object-id",
        "scp": REQUIRED_SCOPE,
        "groups": ["test-commerce-group"],
    }

    claims.update(overrides)

    return jwt.encode(
        claims,
        private_key,
        algorithm="RS256",
        headers={"kid": "test-key-001"},
    )


def test_valid_jwt_accepted(signing_key):
    token = make_token(signing_key)

    identity = auth.verify_access_token(token)

    assert identity.user_id == "test-developer-object-id"
    assert identity.groups == ("test-commerce-group",)


@pytest.mark.parametrize(
    "claim,value",
    [
        ("aud", "another-application"),
        ("iss", "https://untrusted.example.com"),
        ("tid", "another-tenant"),
        ("scp", "User.Read"),
    ],
)
def test_invalid_security_claim_rejected(
    signing_key,
    claim,
    value,
):
    token = make_token(
        signing_key,
        **{claim: value},
    )

    with pytest.raises(auth.AuthenticationError):
        auth.verify_access_token(token)


def test_expired_jwt_rejected(signing_key):
    now = datetime.now(timezone.utc)

    token = make_token(
        signing_key,
        exp=now - timedelta(minutes=5),
    )

    with pytest.raises(auth.AuthenticationError):
        auth.verify_access_token(token)


def test_invalid_signature_rejected(signing_key):
    """
    A token signed with an untrusted private key
    must fail verification.
    """

    attacker_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    token = make_token(attacker_key)

    with pytest.raises(auth.AuthenticationError):
        auth.verify_access_token(token)


def test_group_overage_rejected(signing_key):
    token = make_token(
        signing_key,
        groups=[],
        _claim_names={
            "groups": "src1",
        },
    )

    with pytest.raises(auth.AuthenticationError):
        auth.verify_access_token(token)
