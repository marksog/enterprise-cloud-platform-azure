import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app
from app.policy import PolicyEngineUnavailableError

from app.auth import DeveloperIdentity, get_current_developer
from app.entra_config import COMMERCE_DEVELOPERS_GROUP_ID


client = TestClient(app)

@pytest.fixture(autouse=True)
def authenticated_developer():
    """
    Provide an authenticated developer for workload tests.

    This bypasses external Entra authentication only
    inside the test environment.
    """

    app.dependency_overrides[get_current_developer] = (
        lambda: DeveloperIdentity(
            user_id="test-developer",
            groups=(COMMERCE_DEVELOPERS_GROUP_ID,),
        )
    )

    yield

    app.dependency_overrides.pop(
        get_current_developer,
        None,
    )

@pytest.fixture
def workload():
    return {
        "name": "catalog-api",
        "domain": "commerce",
        "environment": "dev",
        "size": "small",
        "namespace_mode": "dedicated",
        "exposure": "internal",
        "image": "sogplatformacr.azurecr.io/catalog-api:v1",
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

def test_kubernetes_generator_default_probes():
    import sys
    from pathlib import Path
    import yaml

    generator_dir = Path(__file__).resolve().parents[2] / "generator"
    sys.path.insert(0, str(generator_dir))

    from kubernetes_generator import KubernetesGenerator, KubernetesWorkload

    workload = KubernetesWorkload(
        name="inventory-api",
        namespace="sog-dev-commerce-inventory-api",
        image="sogplatformacr.azurecr.io/inventory-api:v1",
        port=8080,
        size="small",
    )

    deployment = yaml.safe_load(
        KubernetesGenerator().generate(workload)["deployment.yaml"]
    )

    container = deployment["spec"]["template"]["spec"]["containers"][0]

    assert container["startupProbe"]["httpGet"]["path"] == "/health"
    assert container["readinessProbe"]["httpGet"]["path"] == "/ready"
    assert container["livenessProbe"]["httpGet"]["path"] == "/health"

    assert all(
        container[probe]["httpGet"]["port"] == "http"
        for probe in ("startupProbe", "readinessProbe", "livenessProbe")
    )


def test_kubernetes_generator_custom_probes():
    import sys
    from pathlib import Path
    import yaml

    generator_dir = Path(__file__).resolve().parents[2] / "generator"
    sys.path.insert(0, str(generator_dir))

    from kubernetes_generator import KubernetesGenerator, KubernetesWorkload

    workload = KubernetesWorkload(
        name="inventory-api",
        namespace="sog-dev-commerce-inventory-api",
        image="sogplatformacr.azurecr.io/inventory-api:v1",
        port=8080,
        size="small",
        startup_path="/startup",
        readiness_path="/api/ready",
        liveness_path="/api/health",
    )

    deployment = yaml.safe_load(
        KubernetesGenerator().generate(workload)["deployment.yaml"]
    )

    container = deployment["spec"]["template"]["spec"]["containers"][0]

    assert container["startupProbe"]["httpGet"]["path"] == "/startup"
    assert container["readinessProbe"]["httpGet"]["path"] == "/api/ready"
    assert container["livenessProbe"]["httpGet"]["path"] == "/api/health"


def test_kubernetes_generator_rejects_invalid_probe_paths():
    import sys
    from pathlib import Path
    import pytest

    generator_dir = Path(__file__).resolve().parents[2] / "generator"
    sys.path.insert(0, str(generator_dir))

    from kubernetes_generator import KubernetesGenerator, KubernetesWorkload

    for invalid_path in ("ready", "/bad path", ""):
        workload = KubernetesWorkload(
            name="inventory-api",
            namespace="sog-dev-commerce-inventory-api",
            image="sogplatformacr.azurecr.io/inventory-api:v1",
            port=8080,
            size="small",
            readiness_path=invalid_path,
        )

        with pytest.raises(ValueError):
            KubernetesGenerator().generate(workload)

def test_invalid_health_probe_returns_422(workload):
    workload["health"] = {
        "readiness_path": "invalid-path"
    }

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 422


@patch("app.main.evaluate_policy", return_value="allow")
def test_custom_health_probes_in_generated_deployment(
    mock_policy, workload, monkeypatch
):
    import sys
    from pathlib import Path
    import yaml

    generator_dir = Path(__file__).resolve().parents[2] / "generator"
    sys.path.insert(0, str(generator_dir))

    from kubernetes_generator import KubernetesGenerator

    generated_deployments = []
    original_generate = KubernetesGenerator.generate

    def capture_generate(self, kubernetes_workload):
        manifests = original_generate(self, kubernetes_workload)
        generated_deployments.append(manifests["deployment.yaml"])
        return manifests

    monkeypatch.setattr(
        KubernetesGenerator,
        "generate",
        capture_generate,
    )

    workload["health"] = {
        "startup_path": "/startup",
        "readiness_path": "/readyz",
        "liveness_path": "/livez",
    }

    response = client.post("/v1/workloads", json=workload)

    assert response.status_code == 200
    mock_policy.assert_called_once()

    files = response.json()["pull_request"]["files"]

    assert any(
        path.endswith("deployment.yaml")
        for path in files
    )

    assert len(generated_deployments) == 1, (
        "The workload endpoint did not invoke the Kubernetes generator"
    )

    deployment = yaml.safe_load(generated_deployments[0])

    container = deployment["spec"]["template"]["spec"]["containers"][0]

    assert container["startupProbe"]["httpGet"]["path"] == "/startup"
    assert container["readinessProbe"]["httpGet"]["path"] == "/readyz"
    assert container["livenessProbe"]["httpGet"]["path"] == "/livez"