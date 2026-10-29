"""
SOG Platform — GitOps Registration Generator

Generates namespace and Argo CD registration changes
without modifying the repository.
"""

from pathlib import Path

import yaml


class GitOpsRegistrationGenerator:

    def __init__(self, repository_root: Path):
        self.repository_root = repository_root.resolve()

    def _append_resource(self, relative_path: str, resource: str) -> str:
        path = self.repository_root / relative_path

        if not path.is_file():
            raise ValueError(f"Kustomization not found: {relative_path}")

        original = path.read_text(encoding="utf-8")
        config = yaml.safe_load(original)

        if config.get("kind") != "Kustomization":
            raise ValueError("Expected Kubernetes Kustomization")

        resources = config.get("resources")

        if not isinstance(resources, list):
            raise ValueError("Invalid Kustomization resources")

        if resource in resources:
            raise ValueError(f"Resource already registered: {resource}")

        resources.append(resource)

        return yaml.safe_dump(config, sort_keys=False)

    def generate(
        self,
        name: str,
        domain: str,
        namespace: str,
        namespace_mode: str,
    ) -> dict[str, str]:

        changes = {}

        if namespace_mode == "dedicated":

            namespace_path = (
                f"gitops/domains/{domain}/{name}-namespace.yaml"
            )

            namespace_manifest = {
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {
                    "name": namespace,
                    "labels": {
                        "sog.io/domain": domain,
                        "sog.io/environment": "nonprod",
                        "sog.io/workload": name,
                        "app.kubernetes.io/managed-by": "argocd",
                    },
                },
            }

            changes[namespace_path] = yaml.safe_dump(
                namespace_manifest,
                sort_keys=False,
            )

            domain_kustomization = (
                f"gitops/domains/{domain}/kustomization.yaml"
            )

            changes[domain_kustomization] = self._append_resource(
                domain_kustomization,
                f"{name}-namespace.yaml",
            )

        application_path = (
            f"gitops/bootstrap/nonprod/{name}-application.yaml"
        )

        application = {
            "apiVersion": "argoproj.io/v1alpha1",
            "kind": "Application",
            "metadata": {
                "name": name,
                "namespace": "argocd",
            },
            "spec": {
                "project": "default",
                "source": {
                    "repoURL": (
                        "https://github.com/marksog/"
                        "enterprise-cloud-platform-azure.git"
                    ),
                    "targetRevision": "main",
                    "path": (
                        f"gitops/workloads/{name}/overlays/nonprod"
                    ),
                },
                "destination": {
                    "server": "https://kubernetes.default.svc",
                    "namespace": namespace,
                },
                "syncPolicy": {
                    "automated": {
                        "prune": True,
                        "selfHeal": True,
                    },
                    "syncOptions": [
                        "CreateNamespace=false"
                    ],
                },
            },
        }

        changes[application_path] = yaml.safe_dump(
            application,
            sort_keys=False,
        )

        bootstrap_kustomization = (
            "gitops/bootstrap/nonprod/kustomization.yaml"
        )

        changes[bootstrap_kustomization] = self._append_resource(
            bootstrap_kustomization,
            f"{name}-application.yaml",
        )

        return changes