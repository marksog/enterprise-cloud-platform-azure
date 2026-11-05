"""Authenticated HTTP client for the SOG Platform API."""

import os

import httpx

from sogctl.auth import get_access_token


API_BASE_URL = os.getenv(
    "SOG_API_URL",
    "http://127.0.0.1:8000",
)


def get_current_identity() -> dict:
    """Get the developer identity verified by the Platform API."""

    token = get_access_token()

    with httpx.Client(timeout=10.0) as client:
        response = client.get(
            f"{API_BASE_URL.rstrip('/')}/v1/me",
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        response.raise_for_status()

        return response.json()

def create_workload(payload: dict) -> dict:
    """Submit an authenticated workload request."""

    token = get_access_token()

    with httpx.Client(timeout=30.0) as client:
        response = client.post(
            f"{API_BASE_URL.rstrip('/')}/v1/workloads",
            json=payload,
            headers={
                "Authorization": f"Bearer {token}",
            },
        )

        response.raise_for_status()
        return response.json()