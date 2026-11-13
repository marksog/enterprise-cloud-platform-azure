"""GitHub application repository factory."""

import os
import re
from dataclasses import dataclass
from pathlib import Path

import httpx

GOLDEN_PATH_ROOT = (
    Path(__file__).resolve().parents[1]
    / "golden-paths"
    / "python-fastapi"
    / "v1"
)

@dataclass(frozen=True)
class CreatedRepository:
    name: str
    full_name: str
    url: str


class RepositoryFactoryError(Exception):
    pass


class RepositoryFactory:
    def __init__(self, github_client):
        self.github = github_client

    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = True,
    ) -> CreatedRepository:

        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{1,38}[a-z0-9])", name):
            raise RepositoryFactoryError("Invalid repository name")

        owner = os.environ["GITHUB_ORGANIZATION"]
        installation_id = os.environ["GITHUB_ORG_INSTALLATION_ID"]
        token = self.github._installation_token(
            installation_id=installation_id
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        payload = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": True,
        }

        try:
            response = httpx.post(
                f"https://api.github.com/orgs/{owner}/repos",
                headers=headers,
                json=payload,
                timeout=30,
            )

            response.raise_for_status()
            data = response.json()

        except httpx.HTTPStatusError as exc:
            raise RepositoryFactoryError(
                f"GitHub repository creation failed: HTTP {exc.response.status_code}"
            ) from exc

        except httpx.RequestError as exc:
            raise RepositoryFactoryError(
                "GitHub API unavailable"
            ) from exc

        created = CreatedRepository(
            name=data["name"],
            full_name=data["full_name"],
            url=data["html_url"],
        )

        try:
            self.populate_repository(created.full_name, token)
        except RepositoryFactoryError as exc:
            raise RepositoryFactoryError(
                f"Repository created at {created.url}, "
                f"but initialization failed: {exc}"
            ) from exc

        return created

    def populate_repository(self, full_name: str, token: str) -> None:
        """Populate a GitHub repository using the FastAPI Golden Path."""

        template_dir = GOLDEN_PATH_ROOT

        if not template_dir.is_dir():
            raise RepositoryFactoryError("Golden Path template not found")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        root = f"https://api.github.com/repos/{full_name}"

        files = [
            path
            for path in template_dir.rglob("*")
            if path.is_file()
            and not any(
                part in {"__pycache__", ".pytest_cache", ".venv"}
                for part in path.relative_to(template_dir).parts
            )
            and path.suffix != ".pyc"
        ]

        if not files:
            raise RepositoryFactoryError("Golden Path contains no files")

        try:
            with httpx.Client(headers=headers, timeout=30) as client:
                repo_response = client.get(root)
                repo_response.raise_for_status()

                branch = repo_response.json()["default_branch"]

                ref_response = client.get(
                    f"{root}/git/ref/heads/{branch}"
                )
                ref_response.raise_for_status()
                parent_sha = ref_response.json()["object"]["sha"]

                commit_response = client.get(
                    f"{root}/git/commits/{parent_sha}"
                )
                commit_response.raise_for_status()

                tree = [
                    {
                        "path": path.relative_to(template_dir).as_posix(),
                        "mode": "100644",
                        "type": "blob",
                        "content": path.read_text(encoding="utf-8"),
                    }
                    for path in files
                ]

                tree_response = client.post(
                    f"{root}/git/trees",
                    json={
                        "base_tree": commit_response.json()["tree"]["sha"],
                        "tree": tree,
                    },
                )
                tree_response.raise_for_status()

                new_commit = client.post(
                    f"{root}/git/commits",
                    json={
                        "message": "chore: initialize FastAPI Golden Path",
                        "tree": tree_response.json()["sha"],
                        "parents": [parent_sha],
                    },
                )
                new_commit.raise_for_status()

                update_response = client.patch(
                    f"{root}/git/refs/heads/{branch}",
                    json={
                        "sha": new_commit.json()["sha"],
                        "force": False,
                    },
                )
                update_response.raise_for_status()

        except (httpx.HTTPError, OSError, UnicodeError, KeyError) as exc:
            raise RepositoryFactoryError(
                f"Failed to populate repository: {exc}"
            ) from exc