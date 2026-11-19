"""Tests for policy-controlled application onboarding."""

import pytest
from fastapi.testclient import TestClient
from types import SimpleNamespace

from app import main
from app.auth import get_current_developer


@pytest.fixture
def client(monkeypatch):
    # Bypass external identity provider for isolated API tests.
    # Return an authenticated developer object through FastAPI DI.
    from app.auth import DeveloperIdentity

    def fake_developer():
        return DeveloperIdentity(
            user_id="test-developer",
            groups=("platform-developers",),
        )

    main.app.dependency_overrides[get_current_developer] = fake_developer

    with TestClient(main.app) as test_client:
        yield test_client

    main.app.dependency_overrides.clear()


@pytest.fixture
def application_payload():
    return {
        "name": "catalog-api",
        "domain": "commerce",
        "environment": "dev",
        "description": "Catalog service",
        "create_repository": False,
    }


def test_preview_does_not_create_repository(
    client, monkeypatch, application_payload
):
    monkeypatch.setattr(main, "evaluate_policy", lambda **kwargs: "allow")

    def forbidden_create(self, **kwargs):
        pytest.fail("Repository must not be created during preview")

    monkeypatch.setattr(
        main.RepositoryFactory,
        "create_repository",
        forbidden_create,
    )

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["repository_url"] is None
    assert body["policy"]["decision"] == "allow"


def test_denied_request_never_creates_repository(
    client, monkeypatch, application_payload
):
    monkeypatch.setattr(main, "evaluate_policy", lambda **kwargs: "deny")

    def forbidden_create(self, **kwargs):
        pytest.fail("Denied requests must not create repositories")

    monkeypatch.setattr(
        main.RepositoryFactory,
        "create_repository",
        forbidden_create,
    )

    application_payload["create_repository"] = True

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["repository_url"] is None
    assert body["policy"]["decision"] == "deny"


def test_approved_request_creates_repository(
    client, monkeypatch, application_payload
):
    monkeypatch.setattr(main, "evaluate_policy", lambda **kwargs: "allow")

    class FakeRepository:
        url = "https://github.com/sog-platform-engineering/catalog-api"

    calls = []

    def fake_create_repository(self, **kwargs):
        calls.append(kwargs)
        return FakeRepository()

    monkeypatch.setattr(
        main.RepositoryFactory,
        "create_repository",
        fake_create_repository,
    )

    application_payload["create_repository"] = True

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is False
    assert body["repository_url"] == FakeRepository.url
    assert len(calls) == 1
    assert calls[0]["name"] == "catalog-api"
    assert calls[0]["private"] is True


def test_opa_unavailable_fails_closed(
    client, monkeypatch, application_payload
):
    from app.policy import PolicyEngineUnavailableError

    def unavailable(**kwargs):
        raise PolicyEngineUnavailableError("OPA unavailable")

    monkeypatch.setattr(main, "evaluate_policy", unavailable)

    def forbidden_create(self, **kwargs):
        pytest.fail("Repository created while OPA was unavailable")

    monkeypatch.setattr(
        main.RepositoryFactory,
        "create_repository",
        forbidden_create,
    )

    application_payload["create_repository"] = True

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 503


def test_requires_approval_never_provisions(
    client, monkeypatch, application_payload
):
    monkeypatch.setattr(
        main,
        "evaluate_policy",
        lambda **kwargs: "requires_approval",
    )

    def forbidden_create(self, **kwargs):
        pytest.fail("Repository created before approval")

    monkeypatch.setattr(
        main.RepositoryFactory,
        "create_repository",
        forbidden_create,
    )

    application_payload["create_repository"] = True

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 200

    body = response.json()

    assert body["policy"]["decision"] == "requires_approval"
    assert body["dry_run"] is True
    assert body["repository_url"] is None


def test_github_failure_returns_502(
    client, monkeypatch, application_payload
):
    from repository_factory import RepositoryFactoryError

    monkeypatch.setattr(
        main,
        "evaluate_policy",
        lambda **kwargs: "allow",
    )

    def failed_create(self, **kwargs):
        raise RepositoryFactoryError("GitHub API unavailable")

    monkeypatch.setattr(
        main.RepositoryFactory,
        "create_repository",
        failed_create,
    )

    application_payload["create_repository"] = True

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 502
    assert "GitHub API unavailable" in response.json()["detail"]


def test_preview_without_side_effects(
    client, monkeypatch, application_payload
):
    """Image provided, no create flags: dry-run PR preview with zero side effects."""
    monkeypatch.setattr(main, "evaluate_policy", lambda **kwargs: "allow")

    application_payload["image"] = "sogplatformacr.azurecr.io/catalog-api:v1"

    fake_changes = {
        "gitops/workloads/catalog-api/base/deployment.yaml": "content"
    }
    monkeypatch.setattr(main.assembler, "build", lambda spec: fake_changes)

    fake_preview = SimpleNamespace(
        branch="platform/onboard-commerce-catalog-api-dev",
        base_branch="main",
        title="feat(platform): onboard catalog-api to commerce/dev",
        body="...",
        files=("gitops/workloads/catalog-api/base/deployment.yaml",),
    )
    monkeypatch.setattr(
        main.github,
        "prepare_pull_request",
        lambda **kw: fake_preview,
    )

    def forbidden_pr(preview, changes):
        pytest.fail("PR must not be created during preview")

    monkeypatch.setattr(main.github, "create_pull_request", forbidden_pr)

    def forbidden_repo(self, **kwargs):
        pytest.fail("Repository must not be created during preview")

    monkeypatch.setattr(
        main.RepositoryFactory, "create_repository", forbidden_repo
    )

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is True
    assert body["status"] == "preview"
    assert body["pull_request"] is not None
    assert body["pull_request"]["dry_run"] is True
    assert body["repository_url"] is None
    assert body["proposed_registry_path"] == "sogplatformacr.azurecr.io/catalog-api"
    assert body["gitops_app_name"] == "catalog-api"
    assert body["namespace"] == "sog-dev-commerce"


def test_platform_pr_requires_image(
    client, monkeypatch, application_payload
):
    """create_platform_pr=True without image must return 422."""
    application_payload["create_platform_pr"] = True
    # No image in payload

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 422
    assert "image" in response.json()["detail"].lower()


def test_successful_full_integration(
    client, monkeypatch, application_payload
):
    """create_repository + create_platform_pr both True: fully_onboarded."""
    monkeypatch.setattr(main, "evaluate_policy", lambda **kwargs: "allow")

    class FakeRepo:
        url = "https://github.com/sog/catalog-api"

    monkeypatch.setattr(
        main.RepositoryFactory,
        "create_repository",
        lambda self, **kw: FakeRepo(),
    )

    fake_changes = {
        "gitops/workloads/catalog-api/base/deployment.yaml": "content"
    }
    monkeypatch.setattr(main.assembler, "build", lambda spec: fake_changes)

    fake_preview = SimpleNamespace(
        branch="platform/onboard-commerce-catalog-api-dev",
        base_branch="main",
        title="feat(platform): onboard catalog-api to commerce/dev",
        body="...",
        files=("gitops/workloads/catalog-api/base/deployment.yaml",),
    )
    monkeypatch.setattr(
        main.github,
        "prepare_pull_request",
        lambda **kw: fake_preview,
    )

    class FakePR:
        number = 42
        url = "https://github.com/sog/platform/pull/42"

    monkeypatch.setattr(
        main.github,
        "create_pull_request",
        lambda preview, changes: FakePR(),
    )

    application_payload["image"] = "sogplatformacr.azurecr.io/catalog-api:v1"
    application_payload["create_repository"] = True
    application_payload["create_platform_pr"] = True

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["dry_run"] is False
    assert body["status"] == "fully_onboarded"
    assert body["repository_url"] == FakeRepo.url
    assert body["pull_request"] is not None
    assert body["pull_request"]["dry_run"] is False
    assert body["pull_request"]["number"] == 42
    assert body["pull_request"]["url"] == FakePR.url
    assert body["partial_failure_reason"] is None


def test_partial_failure_preserves_repository(
    client, monkeypatch, application_payload
):
    """Repository created but PR fails: returns partial_failure, preserves repository URL."""
    monkeypatch.setattr(main, "evaluate_policy", lambda **kwargs: "allow")

    class FakeRepo:
        url = "https://github.com/sog/catalog-api"

    monkeypatch.setattr(
        main.RepositoryFactory,
        "create_repository",
        lambda self, **kw: FakeRepo(),
    )

    fake_changes = {
        "gitops/workloads/catalog-api/base/deployment.yaml": "content"
    }
    monkeypatch.setattr(main.assembler, "build", lambda spec: fake_changes)

    fake_preview = SimpleNamespace(
        branch="platform/onboard-commerce-catalog-api-dev",
        base_branch="main",
        title="feat(platform): onboard catalog-api to commerce/dev",
        body="...",
        files=("gitops/workloads/catalog-api/base/deployment.yaml",),
    )
    monkeypatch.setattr(
        main.github,
        "prepare_pull_request",
        lambda **kw: fake_preview,
    )

    def failing_pr(preview, changes):
        raise main.GitHubChangeError("GitHub API rate limit exceeded")

    monkeypatch.setattr(main.github, "create_pull_request", failing_pr)

    application_payload["image"] = "sogplatformacr.azurecr.io/catalog-api:v1"
    application_payload["create_repository"] = True
    application_payload["create_platform_pr"] = True

    response = client.post("/v1/applications", json=application_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "partial_failure"
    assert body["dry_run"] is False
    assert body["repository_url"] == FakeRepo.url
    assert body["pull_request"] is None
    assert "rate limit" in body["partial_failure_reason"].lower()
