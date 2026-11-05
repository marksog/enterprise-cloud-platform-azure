from unittest.mock import patch

import httpx
from typer.testing import CliRunner

from sogctl.main import app


runner = CliRunner()


def invoke_create(*extra_args):
    return runner.invoke(
        app,
        [
            "workload",
            "create",
            "--name", "payment-api",
            "--domain", "commerce",
            "--environment", "dev",
            "--size", "small",
            *extra_args,
        ],
    )


def allowed_response():
    return {
        "workload": "payment-api",
        "policy": {
            "decision": "allow",
            "reasons": [],
        },
        "pull_request": {
            "repository": "marksog/enterprise-cloud-platform-azure",
            "branch": "platform/onboard-commerce-payment-api-dev",
            "dry_run": True,
        },
    }


def test_authorized_workload():
    with patch(
        "sogctl.main.create_workload",
        return_value=allowed_response(),
    ) as mock_create:

        result = invoke_create()

    assert result.exit_code == 0
    assert "Policy decision: allow" in result.output

    mock_create.assert_called_once_with({
        "name": "payment-api",
        "domain": "commerce",
        "environment": "dev",
        "size": "small",
        "image": "nginx:1.27",
        "port": 80,
    })


def test_default_image_and_port():
    with patch(
        "sogctl.main.create_workload",
        return_value=allowed_response(),
    ) as mock_create:

        result = invoke_create()

    assert result.exit_code == 0

    payload = mock_create.call_args.args[0]

    assert payload["image"] == "nginx:1.27"
    assert payload["port"] == 80


def test_custom_image():
    with patch(
        "sogctl.main.create_workload",
        return_value=allowed_response(),
    ) as mock_create:

        result = invoke_create(
            "--image", "payment-api:v1",
            "--port", "9000",
        )

    assert result.exit_code == 0

    payload = mock_create.call_args.args[0]

    assert payload["image"] == "payment-api:v1"
    assert payload["port"] == 9000


def test_policy_denial():
    denied_response = {
        "workload": "payment-api",
        "policy": {
            "decision": "deny",
            "reasons": ["Developer is not authorized for this domain"],
        },
    }

    with patch(
        "sogctl.main.create_workload",
        return_value=denied_response,
    ):
        result = invoke_create()

    assert result.exit_code == 2
    assert "Policy decision: deny" in result.output


def test_api_connection_failure():
    request = httpx.Request(
        "POST",
        "http://127.0.0.1:8000/v1/workloads",
    )

    with patch(
        "sogctl.main.create_workload",
        side_effect=httpx.ConnectError(
            "Connection refused",
            request=request,
        ),
    ):
        result = invoke_create()

    assert result.exit_code == 1
    assert "API connection failed" in result.output