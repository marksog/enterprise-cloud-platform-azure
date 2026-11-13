"""Tests for policy-controlled application onboarding."""

import pytest
from fastapi.testclient import TestClient

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
