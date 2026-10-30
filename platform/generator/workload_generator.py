import re
from dataclasses import dataclass
from pathlib import Path

import hcl2
import json 


# ============================================================
# SOG PLATFORM — WORKLOAD GENERATOR
# ============================================================

SUPPORTED_ENVIRONMENTS = {"nonprod"}
SUPPORTED_SIZES = {"small", "medium", "large"}
SUPPORTED_NAMESPACE_MODES = {"domain", "dedicated"}
SUPPORTED_WORKLOAD_TYPES = {"stateless-http-api"}

WORKLOAD_NAME_PATTERN = re.compile(
    r"^[a-z][a-z0-9-]*[a-z0-9]$"
)


class WorkloadValidationError(Exception):
    """Raised when workload intent violates the generator contract."""


@dataclass(frozen=True)
class WorkloadSpec:
    name: str
    domain: str
    environment: str
    size: str
    namespace_mode: str
    image: str
    port: int
    workload_type: str = "stateless-http-api"


class WorkloadGenerator:
    """
    Validates developer workload intent against the existing
    SOG platform infrastructure configuration.

    This version reads configuration but does not modify files,
    execute Terraform, or provision Azure resources.
    """

    def __init__(self, repository_root: Path):
        self.repository_root = repository_root.resolve()

    # --------------------------------------------------------
    # Workload validation
    # --------------------------------------------------------

    def validate(self, spec: WorkloadSpec) -> None:

        if not WORKLOAD_NAME_PATTERN.fullmatch(spec.name):
            raise WorkloadValidationError(
                "Invalid workload name"
            )

        if len(spec.name) > 40:
            raise WorkloadValidationError(
                "Workload name exceeds 40 characters"
            )

        if spec.environment not in SUPPORTED_ENVIRONMENTS:
            raise WorkloadValidationError(
                "Unsupported environment"
            )

        if spec.size not in SUPPORTED_SIZES:
            raise WorkloadValidationError(
                "Unsupported workload size"
            )

        if spec.namespace_mode not in SUPPORTED_NAMESPACE_MODES:
            raise WorkloadValidationError(
                "Unsupported namespace mode"
            )

        if spec.workload_type not in SUPPORTED_WORKLOAD_TYPES:
            raise WorkloadValidationError(
                "Unsupported workload type"
            )

        if not 1 <= spec.port <= 65535:
            raise WorkloadValidationError(
                "Invalid application port"
            )

        if not spec.image.strip():
            raise WorkloadValidationError(
                "Container image is required"
            )

        if not WORKLOAD_NAME_PATTERN.fullmatch(spec.domain):
            raise WorkloadValidationError(
                "Invalid domain name"
            )

    # --------------------------------------------------------
    # Namespace resolution
    # --------------------------------------------------------

    def resolve_namespace(self, spec: WorkloadSpec) -> str:

        self.validate(spec)

        domain_namespace = (
            f"sog-{spec.environment}-{spec.domain}"
        )

        if spec.namespace_mode == "domain":
            namespace = domain_namespace
        else:
            namespace = f"{domain_namespace}-{spec.name}"

        if len(namespace) > 63:
            raise WorkloadValidationError(
                "Resolved namespace exceeds 63 characters"
            )

        return namespace

    # --------------------------------------------------------
    # GitOps duplicate detection
    # --------------------------------------------------------

    def check_existing_workload(self, spec: WorkloadSpec) -> None:

        workload_directory = (
            self.repository_root
            / "gitops"
            / "workloads"
            / spec.name
        )

        if workload_directory.exists():
            raise WorkloadValidationError(
                f"Workload '{spec.name}' already exists"
            )

    # --------------------------------------------------------
    # Terraform catalog reader
    # --------------------------------------------------------

    def load_workload_catalog(self) -> dict:
        """
        Read the existing Terraform workload catalog.

        This method never modifies the repository.
        """

        catalog_path = (
            self.repository_root
            / "terraform"
            / "workloads"
            / "nonprod"
            / "workloads.auto.tfvars"
        )

        if not catalog_path.is_file():
            raise WorkloadValidationError(
                f"Terraform workload catalog not found: {catalog_path}"
            )

        try:
            with catalog_path.open("r", encoding="utf-8") as file:
                catalog = hcl2.load(file)

        except (OSError, ValueError) as exc:
            raise WorkloadValidationError(
                "Unable to read or parse Terraform workload catalog"
            ) from exc

        if not isinstance(catalog.get("domains"), dict):
            raise WorkloadValidationError(
                "Invalid Terraform catalog: domains map missing"
            )

        if not isinstance(catalog.get("workloads"), dict):
            raise WorkloadValidationError(
                "Invalid Terraform catalog: workloads map missing"
            )

        catalog["workloads"] = {
            name.strip('"'): configuration
            for name, configuration in catalog["workloads"].items()
        }

        return catalog

    # --------------------------------------------------------
    # Terraform workload registration validation
    # --------------------------------------------------------

    def validate_catalog_registration(self, spec: WorkloadSpec) -> None:
        """
        Verify that:
        1. The workload specification is valid.
        2. The requested domain exists.
        3. The workload is not already registered in Terraform.
        4. The workload does not already exist in GitOps.
        """

        self.validate(spec)
        self.resolve_namespace(spec)

        catalog = self.load_workload_catalog()

        if spec.domain not in catalog["domains"]:
            raise WorkloadValidationError(
                f"Domain '{spec.domain}' is not registered"
            )

        if spec.name in catalog["workloads"]:
            raise WorkloadValidationError(
                f"Workload '{spec.name}' is already registered"
            )

        self.check_existing_workload(spec)
    
        # --------------------------------------------------------
    # Terraform workload entry generation
    # --------------------------------------------------------

    def generate_terraform_entry(self, spec: WorkloadSpec) -> str:
        """
        Generate a Terraform workload declaration in memory.

        This method does not modify repository files.
        """

        self.validate_catalog_registration(spec)

        return (
            f'  "{spec.name}" = {{\n'
            f'    domain         = "{spec.domain}"\n'
            f'    image          = "{spec.image}"\n'
            f'    port           = {spec.port}\n'
            f'    size           = "{spec.size}"\n'
            f'    exposure       = "internal"\n'
            f'    namespace_mode = "{spec.namespace_mode}"\n'
            f'  }}'
        )
    
    def generate_terraform_catalog(self, spec: WorkloadSpec) -> str:
        """
        Generate an updated Terraform workload catalog in memory.

        Preserve existing configuration and insert the new workload
        before the closing brace of the workloads map.
        """
        self.validate_catalog_registration(spec)

        catalog_path = (
            self.repository_root
            / "terraform"
            / "workloads"
            / "nonprod"
            / "workloads.auto.tfvars"
        )

        original = catalog_path.read_text(encoding="utf-8")

        # Find the workloads map.
        match = re.search(r"\bworkloads\s*=\s*\{", original)

        if not match:
            raise WorkloadValidationError(
                "Unable to locate workloads map"
            )

        # Track braces to find the closing brace of the map.
        # This is a temporary renderer for our controlled catalog.
        depth = 1
        position = match.end()

        while position < len(original) and depth > 0:
            character = original[position]

            if character == "{":
                depth += 1
            elif character == "}":
                depth -= 1

            position += 1

        if depth != 0:
            raise WorkloadValidationError(
                "Malformed workloads map"
            )

        insertion_point = position - 1
        entry = self.generate_terraform_entry(spec)

        updated = (
            original[:insertion_point].rstrip()
            + "\n\n"
            + entry
            + "\n"
            + original[insertion_point:]
        )

        # Validate generated HCL.
        try:
            parsed = hcl2.loads(updated)
        except Exception as exc:
            raise WorkloadValidationError(
                "Generated Terraform catalog is invalid"
            ) from exc

        workloads = parsed.get("workloads", {})

        normalized_names = {
            name.strip('"') for name in workloads
        }

        if spec.name not in normalized_names:
            raise WorkloadValidationError(
                "Generated workload entry not found"
            )

        return updated