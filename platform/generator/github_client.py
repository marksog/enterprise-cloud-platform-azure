"""
SOG Platform — GitHub Pull Request Client

Initial implementation:
- Prepares a pull request preview.
- Validates generated file paths.
- Does not create branches, commits, or pull requests.
"""

from dataclasses import dataclass
from pathlib import PurePosixPath


class GitHubChangeError(Exception):
    """Raised when a proposed GitHub change is invalid."""


@dataclass(frozen=True)
class PullRequestPreview:
    branch: str
    base_branch: str
    title: str
    body: str
    files: tuple[str, ...]
    dry_run: bool = True


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