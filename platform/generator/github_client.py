"""
SOG Platform — GitHub Pull Request Client

Supports:
- Pull request previews
- GitHub App authentication
- Git branch creation
- Atomic commits containing generated files
- Real GitHub pull request creation
"""

import os
import time
from dataclasses import dataclass
from pathlib import PurePosixPath

import httpx
import jwt


class GitHubChangeError(Exception):
    """Raised when a GitHub change is invalid or cannot be completed."""


@dataclass(frozen=True)
class PullRequestPreview:
    branch: str
    base_branch: str
    title: str
    body: str
    files: tuple[str, ...]
    dry_run: bool = True


@dataclass(frozen=True)
class CreatedPullRequest:
    number: int
    url: str
    branch: str


class GitHubClient:

    def __init__(self, repository: str, base_branch: str = "main"):
        self.repository = repository
        self.base_branch = base_branch

    def validate_changes(self, changes: dict[str, str]) -> None:
        if not changes:
            raise GitHubChangeError("Change set cannot be empty")

        allowed_roots = {"terraform", "gitops"}

        for path, content in changes.items():
            relative_path = PurePosixPath(path)

            if (
                relative_path.is_absolute()
                or ".." in relative_path.parts
                or relative_path.parts[0] not in allowed_roots
            ):
                raise GitHubChangeError(
                    f"Unsafe generated path: {path}"
                )

            if not isinstance(content, str):
                raise GitHubChangeError(
                    f"Invalid content for {path}"
                )

    def prepare_pull_request(
        self,
        workload_name: str,
        domain: str,
        environment: str,
        changes: dict[str, str],
    ) -> PullRequestPreview:

        self.validate_changes(changes)

        branch = (
            f"platform/onboard-{domain}-{workload_name}-{environment}"
        )

        title = (
            f"feat(platform): onboard {workload_name} "
            f"to {domain}/{environment}"
        )

        body = (
            "## SOG Platform — Automated Workload Onboarding\n\n"
            f"**Workload:** {workload_name}\n"
            f"**Domain:** {domain}\n"
            f"**Environment:** {environment}\n\n"
            "### Generated configuration\n"
            "- Terraform workload registration\n"
            "- Kubernetes Golden Path manifests\n"
            "- Namespace registration\n"
            "- Argo CD Application registration\n\n"
            "### Review requirements\n"
            "- Terraform validation and plan\n"
            "- Kubernetes manifest validation\n"
            "- Platform policy checks\n"
            "- Platform engineering approval\n"
        )

        return PullRequestPreview(
            branch=branch,
            base_branch=self.base_branch,
            title=title,
            body=body,
            files=tuple(sorted(changes)),
        )

    def _installation_token(self) -> str:
        app_id = os.getenv("GITHUB_APP_ID")
        installation_id = os.getenv("GITHUB_APP_INSTALLATION_ID")
        key_path = os.getenv("GITHUB_APP_PRIVATE_KEY_PATH")

        if not all((app_id, installation_id, key_path)):
            raise GitHubChangeError(
                "GitHub App configuration is incomplete"
            )

        try:
            with open(key_path, encoding="utf-8") as key_file:
                private_key = key_file.read()

            now = int(time.time())

            app_jwt = jwt.encode(
                {
                    "iat": now - 60,
                    "exp": now + 540,
                    "iss": app_id,
                },
                private_key,
                algorithm="RS256",
            )

            response = httpx.post(
                (
                    "https://api.github.com/app/installations/"
                    f"{installation_id}/access_tokens"
                ),
                headers={
                    "Authorization": f"Bearer {app_jwt}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=20,
            )

            response.raise_for_status()
            return response.json()["token"]

        except (
            OSError,
            ValueError,
            KeyError,
            jwt.PyJWTError,
            httpx.HTTPError,
        ) as exc:
            raise GitHubChangeError(
                "Unable to obtain GitHub App installation token"
            ) from exc

    def create_pull_request(
        self,
        preview: PullRequestPreview,
        changes: dict[str, str],
    ) -> CreatedPullRequest:
        """
        Create one commit containing generated files,
        create a feature branch, and open a pull request.
        """

        self.validate_changes(changes)

        token = self._installation_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        root = f"https://api.github.com/repos/{self.repository}"

        def request(method, path, *, payload=None, params=None):
            try:
                response = httpx.request(
                    method,
                    root + path,
                    headers=headers,
                    json=payload,
                    params=params,
                    timeout=25,
                )

                response.raise_for_status()
                return response.json()

            except httpx.HTTPStatusError as exc:
                raise GitHubChangeError(
                    f"GitHub {method} {path} returned "
                    f"HTTP {exc.response.status_code}"
                ) from exc

            except httpx.RequestError as exc:
                raise GitHubChangeError(
                    "GitHub API is unreachable"
                ) from exc

        owner = self.repository.split("/", 1)[0]

        # Avoid duplicate open pull requests.
        existing = request(
            "GET",
            "/pulls",
            params={
                "state": "open",
                "head": f"{owner}:{preview.branch}",
                "base": preview.base_branch,
            },
        )

        if existing:
            pr = existing[0]

            return CreatedPullRequest(
                number=pr["number"],
                url=pr["html_url"],
                branch=preview.branch,
            )

        # Retrieve the current base branch.
        base = request(
            "GET",
            f"/git/ref/heads/{preview.base_branch}",
        )

        base_sha = base["object"]["sha"]

        parent = request(
            "GET",
            f"/git/commits/{base_sha}",
        )

        # Build one Git tree containing all generated files.
        tree = request(
            "POST",
            "/git/trees",
            payload={
                "base_tree": parent["tree"]["sha"],
                "tree": [
                    {
                        "path": path,
                        "mode": "100644",
                        "type": "blob",
                        "content": content,
                    }
                    for path, content in sorted(changes.items())
                ],
            },
        )

        # Create one commit.
        commit = request(
            "POST",
            "/git/commits",
            payload={
                "message": preview.title,
                "tree": tree["sha"],
                "parents": [base_sha],
            },
        )

        # Create feature branch. Never write directly to main.
        request(
            "POST",
            "/git/refs",
            payload={
                "ref": f"refs/heads/{preview.branch}",
                "sha": commit["sha"],
            },
        )

        # Ask GitHub to create the pull request.
        pr = request(
            "POST",
            "/pulls",
            payload={
                "title": preview.title,
                "body": preview.body,
                "head": preview.branch,
                "base": preview.base_branch,
            },
        )

        return CreatedPullRequest(
            number=pr["number"],
            url=pr["html_url"],
            branch=preview.branch,
        )