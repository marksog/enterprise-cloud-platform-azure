"""
SOG Platform - Kubernetes Manifest Generator

Generates Kubernetes manifests from approved workload specifications.

This module:
- Does not modify repository files.
- Does not communicate with Kubernetes.
- Does not provision Azure infrastructure.
- Returns deterministic YAML configuration.
"""

from dataclasses import dataclass
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, StrictUndefined


@dataclass(frozen=True)
class KubernetesWorkload:
    name: str
    namespace: str
    image: str
    port: int
    size: str


RESOURCE_PROFILES = {
    "small": {
        "cpu_request": "100m",
        "cpu_limit": "500m",
        "memory_request": "128Mi",
        "memory_limit": "256Mi",
        "replicas": 1,
    },
    "medium": {
        "cpu_request": "250m",
        "cpu_limit": "1000m",
        "memory_request": "256Mi",
        "memory_limit": "1Gi",
        "replicas": 2,
    },
    "large": {
        "cpu_request": "500m",
        "cpu_limit": "2000m",
        "memory_request": "512Mi",
        "memory_limit": "2Gi",
        "replicas": 2,
    },
}


class KubernetesGenerator:
    """Render Kubernetes manifests from approved Golden Path templates."""

    def __init__(self, template_root: Path | None = None):
        if template_root is None:
            template_root = (
                Path(__file__).resolve().parents[1]
                / "golden-paths"
                / "stateless-http-api"
                / "v1"
            )

        self.template_root = template_root

        self.environment = Environment(
            loader=FileSystemLoader(str(template_root)),
            undefined=StrictUndefined,
            autoescape=False,
            keep_trailing_newline=True,
        )

    def generate(self, workload: KubernetesWorkload) -> dict[str, str]:
        if workload.size not in RESOURCE_PROFILES:
            raise ValueError("Unsupported workload size")

        profile = RESOURCE_PROFILES[workload.size]

        templates = (
            "deployment.yaml",
            "service.yaml",
            "serviceaccount.yaml",
            "networkpolicy.yaml",
            "servicemonitor.yaml"
        )

        manifests = {}

        for filename in templates:
            template = self.environment.get_template(f"{filename}.j2")

            manifests[filename] = template.render(
                workload=workload,
                profile=profile,
            )
        manifests["base/kustomization.yaml"] = (
            self.environment
            .get_template("base-kustomization.yaml.j2")
            .render(workload=workload, profile=profile)
        )

        manifests["overlays/nonprod/kustomization.yaml"] = (
            self.environment
            .get_template("overlay-kustomization.yaml.j2")
            .render(workload=workload, profile=profile)
        )
        return manifests