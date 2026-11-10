from enum import Enum

from pydantic import BaseModel, Field, field_validator

class WorkloadSize(str, Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

class NamespaceMode(str, Enum):
    DOMAIN = "domain"
    DEDICATED = "dedicated" 

class Exposure(str, Enum):
    INTERNAL = "internal"
    PUBLIC = "public"

class HealthProbeConfig(BaseModel):
    startup_path: str = "/health"
    readiness_path: str = "/ready"
    liveness_path: str = "/health"

    @field_validator(
        "startup_path",
        "readiness_path",
        "liveness_path",
    )
    @classmethod
    def validate_probe_path(cls, value: str) -> str:
        if (
            not value.startswith("/")
            or len(value) > 256
            or any(character.isspace() for character in value)
        ):
            raise ValueError(
                "Probe path must start with '/', "
                "contain no whitespace, and be at most 256 characters"
            )

        return value

class WorkloadRequest(BaseModel):
    name: str = Field(
        min_length=3,
        max_length=40,
        pattern=r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?$"
    )

    domain: str
    environment: str

    size: WorkloadSize = WorkloadSize.SMALL
    namespace_mode: NamespaceMode = NamespaceMode.DOMAIN
    exposure: Exposure = Exposure.INTERNAL

    image: str 
    port: int = Field(default=8080, ge=1, le=65535)

    justification: str | None = None

    create_pull_request: bool = False

    health: HealthProbeConfig = Field(default_factory=HealthProbeConfig)

class PolicyDecision(BaseModel):
    decision: str
    reasons: list[str] = Field(default_factory=list)

class PullRequestPreviewResponse(BaseModel):
    repository: str
    branch: str
    base_branch: str
    title: str
    files: list[str]
    dry_run: bool
    number: int | None = None
    url: str | None = None

class WorkloadResponse(BaseModel):
    workload: str
    domain: str
    environment: str
    policy: PolicyDecision
    pull_request: PullRequestPreviewResponse | None = None

class HealthProbeConfig(BaseModel):
    startup_path: str = "/health"
    readiness_path: str = "/ready"
    liveness_path: str = "/health"

    @field_validator(
        "startup_path",
        "readiness_path",
        "liveness_path",
    )
    @classmethod
    def validate_probe_path(cls, value: str) -> str:
        if (
            not value.startswith("/")
            or len(value) > 256
            or any(character.isspace() for character in value)
        ):
            raise ValueError(
                "Probe path must start with '/', "
                "contain no whitespace, and be at most 256 characters"
            )

        return value
