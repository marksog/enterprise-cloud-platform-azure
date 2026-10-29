import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.policy import PolicyEngineUnavailableError


client = TestClient(app)


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


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("app.main.evaluate_policy", return_value="allow")
def test_authorized_workload(mock_policy, workload):
    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 200

    data = response.json()

    assert data["policy"]["decision"] == "allow"
    assert data["pull_request"]["dry_run"] is True
    assert len(data["pull_request"]["files"]) == 12


@patch("app.main.evaluate_policy", return_value="deny")
def test_unauthorized_domain(mock_policy, workload):
    workload["domain"] = "healthcare"

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 200
    assert response.json()["policy"]["decision"] == "deny"
    assert response.json()["pull_request"] is None


@patch(
    "app.main.evaluate_policy",
    return_value="requires_approval",
)
def test_large_workload_requires_approval(mock_policy, workload):
    workload["size"] = "large"
    workload["justification"] = "Expected high processing demand"

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 200
    assert response.json()["policy"]["decision"] == "requires_approval"
    assert response.json()["pull_request"] is None


@patch("app.main.evaluate_policy")
def test_opa_unavailable(mock_policy, workload):
    mock_policy.side_effect = PolicyEngineUnavailableError(
        "OPA unavailable"
    )

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 503
    assert "Policy engine unavailable" in response.json()["detail"]


@patch("app.main.evaluate_policy", return_value="allow")
def test_duplicate_workload(mock_policy, workload):
    workload["name"] = "payments-api"

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 422
    assert "already registered" in response.json()["detail"] 