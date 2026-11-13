"""Mocked integration tests for the GitHub Repository Factory."""

import sys
from pathlib import Path
from unittest.mock import Mock

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import repository_factory as factory_module
from repository_factory import (
    RepositoryFactory,
    RepositoryFactoryError,
)


@pytest.fixture
def github_client():
    client = Mock()
    client._installation_token.return_value = "test-installation-token"
    return client


@pytest.fixture
def factory(github_client):
    return RepositoryFactory(github_client)


def test_invalid_repository_name_is_rejected(factory):
    with pytest.raises(RepositoryFactoryError):
        factory.create_repository("INVALID NAME")


def test_populate_repository_creates_git_commit(
    factory, monkeypatch, tmp_path
):
    template = tmp_path / "golden-path"
    template.mkdir()

    (template / "README.md").write_text("# Generated application")

    app_dir = template / "app"
    app_dir.mkdir()

    (app_dir / "main.py").write_text(
        "from fastapi import FastAPI\napp = FastAPI()\n"
    )

    monkeypatch.setattr(
        factory_module,
        "GOLDEN_PATH_ROOT",
        template,
    )

    requests = []

    def handler(request):
        requests.append(request)

        path = request.url.path

        if path == "/repos/sog-platform-engineering/catalog-api":
            return httpx.Response(
                200,
                json={"default_branch": "main"},
            )

        if path.endswith("/git/ref/heads/main"):
            return httpx.Response(
                200,
                json={"object": {"sha": "parent-sha"}},
            )

        if path.endswith("/git/commits/parent-sha"):
            return httpx.Response(
                200,
                json={"tree": {"sha": "base-tree-sha"}},
            )

        if path.endswith("/git/trees"):
            return httpx.Response(
                201,
                json={"sha": "new-tree-sha"},
            )

        if path.endswith("/git/commits"):
            return httpx.Response(
                201,
                json={"sha": "new-commit-sha"},
            )

        if path.endswith("/git/refs/heads/main"):
            return httpx.Response(200, json={})

        return httpx.Response(404)

    transport = httpx.MockTransport(handler)

    original_client = httpx.Client

    def mocked_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_client(*args, **kwargs)

    monkeypatch.setattr(
        factory_module.httpx,
        "Client",
        mocked_client,
    )

    factory.populate_repository(
        "sog-platform-engineering/catalog-api",
        "test-token",
    )

    methods = [request.method for request in requests]

    assert methods == [
        "GET",
        "GET",
        "GET",
        "POST",
        "POST",
        "PATCH",
    ]

    tree_request = requests[3]
    tree_payload = __import__("json").loads(tree_request.content)

    paths = [entry["path"] for entry in tree_payload["tree"]]

    assert "README.md" in paths
    assert "app/main.py" in paths

    commit_request = requests[4]
    commit_payload = __import__("json").loads(commit_request.content)

    assert commit_payload["parents"] == ["parent-sha"]
    assert commit_payload["tree"] == "new-tree-sha"

    update_request = requests[5]
    update_payload = __import__("json").loads(update_request.content)

    assert update_payload["sha"] == "new-commit-sha"
    assert update_payload["force"] is False


def test_create_repository_success(factory, monkeypatch):
    """Successful creation must initialize the repository."""

    monkeypatch.setenv(
        "GITHUB_ORGANIZATION", "sog-platform-engineering"
    )
    monkeypatch.setenv(
        "GITHUB_ORG_INSTALLATION_ID", "181324843"
    )

    requests = []

    def fake_post(url, **kwargs):
        requests.append((url, kwargs))
        return httpx.Response(
            201,
            request=httpx.Request("POST", url),
            json={
                "name": "catalog-api",
                "full_name": "sog-platform-engineering/catalog-api",
                "html_url": (
                    "https://github.com/"
                    "sog-platform-engineering/catalog-api"
                ),
            },
        )

    monkeypatch.setattr(factory_module.httpx, "post", fake_post)

    initialized = []

    monkeypatch.setattr(
        factory,
        "populate_repository",
        lambda full_name, token: initialized.append(
            (full_name, token)
        ),
    )

    result = factory.create_repository(
        name="catalog-api",
        description="Catalog service",
    )

    assert result.name == "catalog-api"
    assert result.full_name == "sog-platform-engineering/catalog-api"

    assert len(requests) == 1

    url, kwargs = requests[0]

    assert url == (
        "https://api.github.com/"
        "orgs/sog-platform-engineering/repos"
    )

    assert kwargs["json"]["private"] is True
    assert kwargs["json"]["auto_init"] is True

    assert initialized == [
        (
            "sog-platform-engineering/catalog-api",
            "test-installation-token",
        )
    ]


@pytest.mark.parametrize("status_code", [401, 403, 422])
def test_create_repository_http_failure(
    factory, monkeypatch, status_code
):
    """GitHub errors must not trigger template initialization."""

    monkeypatch.setenv(
        "GITHUB_ORGANIZATION", "sog-platform-engineering"
    )
    monkeypatch.setenv(
        "GITHUB_ORG_INSTALLATION_ID", "181324843"
    )

    def fake_post(url, **kwargs):
        return httpx.Response(
            status_code,
            request=httpx.Request("POST", url),
            json={"message": "GitHub rejected request"},
        )

    monkeypatch.setattr(factory_module.httpx, "post", fake_post)

    def forbidden_populate(*args, **kwargs):
        pytest.fail("Initialized repository after GitHub failure")

    monkeypatch.setattr(
        factory,
        "populate_repository",
        forbidden_populate,
    )

    with pytest.raises(
        RepositoryFactoryError,
        match=f"HTTP {status_code}",
    ):
        factory.create_repository("catalog-api")


def test_create_repository_timeout(factory, monkeypatch):
    """Network timeouts must produce controlled failures."""

    monkeypatch.setenv(
        "GITHUB_ORGANIZATION", "sog-platform-engineering"
    )
    monkeypatch.setenv(
        "GITHUB_ORG_INSTALLATION_ID", "181324843"
    )

    def fake_post(url, **kwargs):
        raise httpx.ConnectTimeout("Connection timed out")

    monkeypatch.setattr(factory_module.httpx, "post", fake_post)

    with pytest.raises(
        RepositoryFactoryError,
        match="GitHub API unavailable",
    ):
        factory.create_repository("catalog-api")


def test_partial_repository_creation(factory, monkeypatch):
    """Initialization failure must not be reported as success."""

    monkeypatch.setenv(
        "GITHUB_ORGANIZATION", "sog-platform-engineering"
    )
    monkeypatch.setenv(
        "GITHUB_ORG_INSTALLATION_ID", "181324843"
    )

    def fake_post(url, **kwargs):
        return httpx.Response(
            201,
            request=httpx.Request("POST", url),
            json={
                "name": "catalog-api",
                "full_name": "sog-platform-engineering/catalog-api",
                "html_url": (
                    "https://github.com/"
                    "sog-platform-engineering/catalog-api"
                ),
            },
        )

    monkeypatch.setattr(factory_module.httpx, "post", fake_post)

    def failed_initialization(*args, **kwargs):
        raise RepositoryFactoryError("Git tree creation failed")

    monkeypatch.setattr(
        factory,
        "populate_repository",
        failed_initialization,
    )

    with pytest.raises(
        RepositoryFactoryError,
        match="initialization failed",
    ) as exc:
        factory.create_repository("catalog-api")

    assert "catalog-api" in str(exc.value)
    assert "Git tree creation failed" in str(exc.value)
