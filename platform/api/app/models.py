from enum import Enum

from pydantic import BaseModel, Field

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

class WorkloadResponse(BaseModel):
    workload: str
    domain: str
    environment: str
    policy: PolicyDecision
    pull_request: PullRequestPreviewResponse | None = None

