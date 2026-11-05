from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.auth import DeveloperIdentity, get_current_developer
from app.entra_config import COMMERCE_DEVELOPERS_GROUP_ID
from app.main import app


client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_dependency_overrides():
    """Ensure each security test starts without authentication overrides."""
    previous = app.dependency_overrides.copy()
    app.dependency_overrides.clear()

    yield

    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous)


@pytest.fixture
def workload():
    return {
        "name": "inventory-api",
        "domain": "commerce",
        "environment": "nonprod",
        "size": "small",
        "namespace_mode": "dedicated",
        "exposure": "internal",
        "image": "sogplatformacr.azurecr.io/inventory-api:v1",
        "port": 8080,
    }


def test_unauthenticated_request_rejected(workload):
    """Requests without bearer tokens must be rejected."""

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 401


@patch("app.main.evaluate_policy")
def test_unauthorized_developer_cannot_generate_infrastructure(
    mock_policy, workload
):
    """Unknown Entra groups must not grant infrastructure permissions."""

    app.dependency_overrides[get_current_developer] = (
        lambda: DeveloperIdentity(
            user_id="unauthorized-developer",
            groups=("unknown-security-group",),
        )
    )

    def enforce_test_policy(*, workload, identity):
        if "commerce-developers" not in identity["groups"]:
            return "deny"
        return "allow"

    mock_policy.side_effect = enforce_test_policy

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 200
    assert response.json()["policy"]["decision"] == "deny"
    assert response.json()["pull_request"] is None

    mock_policy.assert_called_once()


@patch("app.main.evaluate_policy", return_value="deny")
def test_verified_identity_propagated_to_opa(mock_policy, workload):
    """OPA must receive the authenticated developer's mapped identity."""

    app.dependency_overrides[get_current_developer] = (
        lambda: DeveloperIdentity(
            user_id="verified-developer-123",
            groups=(COMMERCE_DEVELOPERS_GROUP_ID,),
        )
    )

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 200

    mock_policy.assert_called_once()

    _, kwargs = mock_policy.call_args

    assert kwargs["identity"] == {
        "id": "verified-developer-123",
        "groups": ["commerce-developers"],
    }