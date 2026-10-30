"""
SOG Platform - Generated Change Set Validation

Validates generated Terraform and GitOps configuration
in an isolated temporary repository.

Does not modify the working repository.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path

import hcl2
import yaml

from change_set import ChangeSetAssembler
from workload_generator import WorkloadSpec


def run_command(command: list[str], cwd: Path) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed: {' '.join(command)}\n"
            f"{result.stderr}\n{result.stdout}"
        )

    return result.stdout


def validate_change_set(repository_root: Path, spec: WorkloadSpec):
    assembler = ChangeSetAssembler(repository_root)

    changes = assembler.build(spec)

    with tempfile.TemporaryDirectory(prefix="sog-validation-") as temp:
        validation_root = Path(temp)

        # Copy only the configuration trees needed for validation.
        for directory in ("terraform", "gitops"):
            source = repository_root / directory

            if source.exists():
                shutil.copytree(
                    source,
                    validation_root / directory,
                )

        # Apply proposed changes only to the temporary copy.
        for relative_path, content in changes.items():
            destination = validation_root / relative_path

            if destination.exists():
                # Existing files may be updated by the generator.
                pass

            destination.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            destination.write_text(
                content,
                encoding="utf-8",
            )

        # Validate Terraform HCL syntax and workload registration.
        catalog_path = (
            validation_root
            / "terraform/workloads/nonprod/workloads.auto.tfvars"
        )

        with catalog_path.open(encoding="utf-8") as file:
            catalog = hcl2.load(file)

        workload_names = {
            name.strip('"')
            for name in catalog["workloads"]
        }

        assert spec.name in workload_names

        print("PASS: Terraform catalog parses successfully")

        # Validate generated workload overlay with Kustomize.
        workload_overlay = (
            validation_root
            / "gitops/workloads"
            / spec.name
            / "overlays/nonprod"
        )

        rendered = run_command(
            ["kubectl", "kustomize", str(workload_overlay)],
            validation_root,
        )

        resources = list(yaml.safe_load_all(rendered))

        kinds = {resource["kind"] for resource in resources}

        assert "Deployment" in kinds
        assert "Service" in kinds
        assert "ServiceAccount" in kinds
        assert "NetworkPolicy" in kinds
        assert "ServiceMonitor" in kinds

        print("PASS: Kubernetes overlay renders successfully")

        # Validate domain namespace registration.
        domain_path = (
            validation_root
            / "gitops/domains"
            / spec.domain
        )

        run_command(
            ["kubectl", "kustomize", str(domain_path)],
            validation_root,
        )

        print("PASS: Domain Kustomization renders successfully")

        # Validate Argo CD bootstrap registration.
        bootstrap_path = (
            validation_root
            / "gitops/bootstrap/nonprod"
        )

        run_command(
            ["kubectl", "kustomize", str(bootstrap_path)],
            validation_root,
        )

        print("PASS: Argo CD bootstrap renders successfully")

        print("\nSOG COMPLETE CHANGE SET VALIDATION: PASSED")


if __name__ == "__main__":
    repository_root = Path(__file__).resolve().parents[2]

    spec = WorkloadSpec(
        name="inventory-api",
        domain="commerce",
        environment="nonprod",
        size="small",
        namespace_mode="dedicated",
        image="sogplatformacr.azurecr.io/inventory-api:v1",
        port=8080,
    )

    validate_change_set(repository_root, spec)