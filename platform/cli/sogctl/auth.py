"""Microsoft Entra authentication for the SOG developer CLI."""

import os

import msal
import subprocess
import sys
import keyring


TENANT_ID = os.getenv(
    "SOG_ENTRA_TENANT_ID",
    "b854e21e-defb-4268-8398-05ca9757a1af",
)

CLI_CLIENT_ID = os.getenv(
    "SOG_ENTRA_CLI_CLIENT_ID",
    "f27264cb-4e12-4c1a-9b25-b217d985bbdf",
)

API_CLIENT_ID = os.getenv(
    "SOG_ENTRA_API_CLIENT_ID",
    "c705d7f9-8c81-4649-88b4-55b530b50353",
)

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"

SCOPES = [
    f"api://{API_CLIENT_ID}/access_as_user"
]


KEYCHAIN_SERVICE = "sogctl-msal-cache"
KEYCHAIN_ACCOUNT = f"{TENANT_ID}:{CLI_CLIENT_ID}"


def _read_cache() -> msal.SerializableTokenCache:
    """Load MSAL credentials from the operating system's credential store."""

    cache = msal.SerializableTokenCache()

    stored = keyring.get_password(
        KEYCHAIN_SERVICE,
        KEYCHAIN_ACCOUNT,
    )

    if stored:
        try:
            cache.deserialize(stored)
        except ValueError as exc:
            raise RuntimeError(
                "Invalid cached credentials. "
                "Run 'sogctl logout' and sign in again."
            ) from exc

    return cache


def _write_cache(cache: msal.SerializableTokenCache) -> None:
    """Save MSAL credentials to the operating system's credential store."""

    if not cache.has_state_changed:
        return

    keyring.set_password(
        KEYCHAIN_SERVICE,
        KEYCHAIN_ACCOUNT,
        cache.serialize(),
    )


def _client(
    cache: msal.SerializableTokenCache,
) -> msal.PublicClientApplication:
    return msal.PublicClientApplication(
        client_id=CLI_CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )


def login() -> dict:
    """Authenticate and persist credentials securely."""

    cache = _read_cache()
    client = _client(cache)

    result = client.acquire_token_interactive(
        scopes=SCOPES,
        port=0,
        prompt="select_account",
    )

    if "access_token" not in result:
        raise RuntimeError(
            "Microsoft Entra login failed: "
            + result.get(
                "error_description",
                result.get("error", "unknown error"),
            )
        )

    _write_cache(cache)

    return {
        "username": result.get(
            "id_token_claims", {}
        ).get("preferred_username", "unknown"),
        "scopes": result.get("scope", ""),
    }


def get_access_token() -> str:
    """Acquire an access token silently using cached credentials."""

    cache = _read_cache()
    client = _client(cache)

    accounts = client.get_accounts()

    if not accounts:
        raise RuntimeError(
            "Not signed in. Run 'sogctl login' first."
        )

    result = client.acquire_token_silent(
        SCOPES,
        account=accounts[0],
    )

    _write_cache(cache)

    if not result or "access_token" not in result:
        raise RuntimeError(
            "Unable to acquire a token silently. "
            "Run 'sogctl login' again."
        )

    return result["access_token"]


def logout() -> None:
    """Remove locally cached Microsoft Entra credentials."""

    try:
        keyring.delete_password(
            KEYCHAIN_SERVICE,
            KEYCHAIN_ACCOUNT,
        )
    except keyring.errors.PasswordDeleteError:
        pass