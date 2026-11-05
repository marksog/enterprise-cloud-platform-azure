from unittest.mock import patch

import httpx
import pytest
from httpx import Client as RealHttpxClient

from sogctl.client import create_workload


def test_create_workload_sends_bearer_token():
    payload = {
        "name": "payment-api",
        "domain": "commerce",
        "environment": "dev",
        "size": "small",
        "image": "nginx:1.27",
        "port": 80,
    }

    def handler(request):
        assert request.method == "POST"
        assert request.url.path == "/v1/workloads"
        assert request.headers["Authorization"] == "Bearer test-token"
        assert request.headers["Content-Type"] == "application/json"

        return httpx.Response(
            200,
            json={
                "workload": "payment-api",
                "policy": {"decision": "allow"},
            },
        )

    transport = httpx.MockTransport(handler)

    with patch(
        "sogctl.client.get_access_token",
        return_value="test-token",
    ):
        with patch(
            "sogctl.client.httpx.Client",
            side_effect=lambda **kwargs: RealHttpxClient(
                transport=transport,
                **kwargs,
            ),
        ):
            result = create_workload(payload)

    assert result["policy"]["decision"] == "allow"


def test_create_workload_raises_on_http_error():
    def handler(request):
        return httpx.Response(
            401,
            json={"detail": "Unauthorized"},
        )

    transport = httpx.MockTransport(handler)

    with patch(
        "sogctl.client.get_access_token",
        return_value="invalid-token",
    ):
        with patch(
            "sogctl.client.httpx.Client",
            side_effect=lambda **kwargs: RealHttpxClient(
                transport=transport,
                **kwargs,
            ),
        ):
            with pytest.raises(httpx.HTTPStatusError) as exc:
                create_workload({"name": "payment-api"})

    assert exc.value.response.status_code == 401