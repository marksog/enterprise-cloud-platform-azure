"""
SOG Platform - Change Set Assembler

Combines Terraform and Kubernetes configuration generated
from a validated workload specification.

This module does not modify repository files.
"""

from pathlib import Path

from kubernetes_generator import (
    KubernetesGenerator,
    KubernetesWorkload,
)

from workload_generator import (
    WorkloadGenerator,
    WorkloadSpec,
)

from gitops_registration import GitOpsRegistrationGenerator


class ChangeSetAssembler:
    """Assemble proposed infrastructure configuration changes."""

    def __init__(self, repository_root: Path):
        self.repository_root = repository_root.resolve()

        self.terraform_generator = WorkloadGenerator(
            self.repository_root
        )

        self.kubernetes_generator = KubernetesGenerator()
    
        self.gitops_generator = GitOpsRegistrationGenerator(
            self.repository_root
        )

    def build(self, spec: WorkloadSpec) -> dict[str, str]:
        """
        Generate proposed Terraform and Kubernetes changes.

        All paths are relative to the repository root.
        No files are written.
        """

        # Validate against the existing workload catalog.
        self.terraform_generator.validate_catalog_registration(spec)

        # Resolve the Kubernetes namespace.
        namespace = self.terraform_generator.resolve_namespace(spec)

        # Generate the complete proposed Terraform catalog.
        terraform_catalog = (
            self.terraform_generator.generate_terraform_catalog(spec)
        )

        # Convert the workload contract for Kubernetes rendering.
        kubernetes_workload = KubernetesWorkload(
            name=spec.name,
            namespace=namespace,
            image=spec.image,
            port=spec.port,
            size=spec.size,
        )

        manifests = self.kubernetes_generator.generate(
            kubernetes_workload
        )

        changes = {
            "terraform/workloads/nonprod/workloads.auto.tfvars":
                terraform_catalog
        }

        workload_root = f"gitops/workloads/{spec.name}"

        for filename, content in manifests.items():

            # Kustomization files already include their directories.
            if filename.startswith(("base/", "overlays/")):
                relative_path = filename
            else:
                relative_path = f"base/{filename}"

            changes[f"{workload_root}/{relative_path}"] = content

        registration_changes = self.gitops_generator.generate(
            name=spec.name,
            domain=spec.domain,
            namespace=namespace,
            namespace_mode=spec.namespace_mode,
        )

        for path, content in registration_changes.items():
            if path in changes:
                raise ValueError(
                    f"Duplicate generated path: {path}"
                )

            changes[path] = content

        return changes