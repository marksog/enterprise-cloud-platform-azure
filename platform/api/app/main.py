"""
SOG Developer Platform API

Local development version.

This API:
- Validates developer workload intent.
- Evaluates policy through OPA.
- Generates infrastructure configuration in memory.
- Prepares GitHub Pull Request previews.

It does not provision infrastructure or modify GitHub.
"""

import os
import sys
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from app.auth import DeveloperIdentity, get_current_developer
from app.identity_mapping import map_developer_identity
from repository_factory import RepositoryFactory, RepositoryFactoryError

from app.models import (
    PolicyDecision,
    PullRequestPreviewResponse,
    WorkloadRequest,
    WorkloadResponse,
    ApplicationRequest,
    ApplicationResponse,
)

from app.policy import (
    PolicyEngineUnavailableError,
    evaluate_policy,
)


# --------------------------------------------------
# Repository and generator imports
# --------------------------------------------------

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

GENERATOR_PATH = REPOSITORY_ROOT / "platform" / "generator"

sys.path.insert(0, str(GENERATOR_PATH))

from change_set import ChangeSetAssembler
from github_client import GitHubClient, GitHubChangeError
from workload_generator import WorkloadSpec, WorkloadValidationError


# --------------------------------------------------
# Application configuration
# --------------------------------------------------

app = FastAPI(
    title="SOG Developer Platform API",
    description="Policy-driven self-service infrastructure platform",
    version="0.3.0",
)

assembler = ChangeSetAssembler(REPOSITORY_ROOT)

github = GitHubClient(
    repository="marksog/enterprise-cloud-platform-azure",
)


# --------------------------------------------------
# Health endpoint
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "service": "sog-platform-api",
        "status": "healthy",
        "version": "0.3.0",
    }

# --------------------------------------------------
# Authenticated developer identity
# --------------------------------------------------

@app.get("/v1/me")
def get_my_identity(
    developer: DeveloperIdentity = Depends(get_current_developer),
):
    identity = map_developer_identity(developer)

    return {
        "developer_id": identity["id"],
        "groups": identity["groups"],
    }

import os

import httpx
from fastapi import Response

OPA_URL = os.getenv(
    "OPA_URL",
    "http://127.0.0.1:8181/v1/data/sog/workload/decision",
)


@app.get("/ready")
async def readiness(response: Response):
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            opa_response = await client.post(
                OPA_URL,
                json={
                    "input": {
                        "identity": {"groups": []},
                        "workload": {},
                    }
                },
            )

            opa_response.raise_for_status()
            result = opa_response.json()

            if "result" not in result:
                response.status_code = 503
                return {
                    "status": "not_ready",
                    "reason": "authorization_policy_unavailable",
                }

            return {
                "status": "ready",
                "dependencies": {
                    "opa": "ready",
                },
            }

    except (
        httpx.RequestError,
        httpx.HTTPStatusError,
        ValueError,
    ):
        response.status_code = 503

        return {
            "status": "not_ready",
            "reason": "policy_engine_unavailable",
        }

# --------------------------------------------------
# Workload onboarding
# --------------------------------------------------

@app.post(
    "/v1/workloads",
    response_model=WorkloadResponse,
)
def create_workload(
    request: WorkloadRequest,
    developer: DeveloperIdentity = Depends(get_current_developer),
):

    identity = map_developer_identity(developer)

    # Step 1: Evaluate organizational policy.
    try:
        decision = evaluate_policy(
            workload=request.model_dump(mode="json"),
            identity = identity,
        )

    except PolicyEngineUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Policy engine unavailable; request not approved",
        ) from exc

    policy = PolicyDecision(
        decision=decision,
        reasons=[],
    )

    # Step 2: Never generate infrastructure for denied
    # or approval-required requests.
    if decision != "allow":
        return WorkloadResponse(
            workload=request.name,
            domain=request.domain,
            environment=request.environment,
            policy=policy,
            pull_request=None,
        )

    # Step 3: Convert API request to generator contract.
    spec = WorkloadSpec(
        name=request.name,
        domain=request.domain,
        environment=request.environment,
        size=request.size.value,
        namespace_mode=request.namespace_mode.value,
        image=request.image,
        port=request.port,
        startup_path=request.health.startup_path,
        readiness_path=request.health.readiness_path,
        liveness_path=request.health.liveness_path,
    )

    # Step 4: Generate Terraform and GitOps configuration.
    try:
        changes = assembler.build(spec)

        # Step 5: Prepare GitHub PR preview.
        preview = github.prepare_pull_request(
            workload_name=spec.name,
            domain=spec.domain,
            environment=spec.environment,
            changes=changes,
        )

    except (WorkloadValidationError, GitHubChangeError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    created_pr = None
    if request.create_pull_request:
        try:
            created_pr = github.create_pull_request(preview, changes)

        except GitHubChangeError as exc:
            raise HTTPException(
                status_code=502,
                detail=str(exc),
            ) from exc

    # Step 6: Return proposed changes.
    return WorkloadResponse(
        workload=request.name,
        domain=request.domain,
        environment=request.environment,
        policy=policy,
        pull_request=PullRequestPreviewResponse(
            repository=github.repository,
            branch=preview.branch,
            base_branch=preview.base_branch,
            title=preview.title,
            files=list(preview.files),
            dry_run=created_pr is None,
            number=created_pr.number if created_pr else None,
            url=created_pr.url if created_pr else None,
        ),
    )

@app.post(
    "/v1/applications",
    response_model=ApplicationResponse,
)
def create_application(
    request: ApplicationRequest,
    developer: DeveloperIdentity = Depends(get_current_developer),
):
    identity = map_developer_identity(developer)

    # Validate early: image required for platform PR creation.
    if request.create_platform_pr and not request.image:
        raise HTTPException(
            status_code=422,
            detail="image is required when create_platform_pr is True",
        )

    # Evaluate policy before any provisioning.
    try:
        decision = evaluate_policy(
            workload={
                "name": request.name,
                "domain": request.domain,
                "environment": request.environment,
                "size": request.size.value,
                "namespace_mode": request.namespace_mode.value,
                "exposure": request.exposure.value,
            },
            identity=identity,
        )
    except PolicyEngineUnavailableError as exc:
        raise HTTPException(
            status_code=503,
            detail="Policy engine unavailable; request not approved",
        ) from exc

    policy = PolicyDecision(decision=decision, reasons=[])

    # Compute derived metadata.
    if request.namespace_mode.value == "dedicated":
        namespace = (
            f"sog-{request.environment}-{request.domain}-{request.name}"
        )
    else:
        namespace = f"sog-{request.environment}-{request.domain}"

    proposed_registry_path = f"sogplatformacr.azurecr.io/{request.name}"
    gitops_app_name = request.name

    # Denied / approval-required: return early, never provision.
    if decision != "allow":
        return ApplicationResponse(
            application=request.name,
            domain=request.domain,
            environment=request.environment,
            policy=policy,
            dry_run=True,
            status=decision,
            namespace=namespace,
            proposed_registry_path=proposed_registry_path,
            gitops_app_name=gitops_app_name,
        )

    # Pure preview: no create flags set.
    if not request.create_repository and not request.create_platform_pr:
        pr_preview = None

        if request.image:
            try:
                spec = WorkloadSpec(
                    name=request.name,
                    domain=request.domain,
                    environment=request.environment,
                    size=request.size.value,
                    namespace_mode=request.namespace_mode.value,
                    image=request.image,
                    port=request.port,
                    startup_path=request.health.startup_path,
                    readiness_path=request.health.readiness_path,
                    liveness_path=request.health.liveness_path,
                )
                changes = assembler.build(spec)
                preview = github.prepare_pull_request(
                    workload_name=spec.name,
                    domain=spec.domain,
                    environment=spec.environment,
                    changes=changes,
                )
                pr_preview = PullRequestPreviewResponse(
                    repository=github.repository,
                    branch=preview.branch,
                    base_branch=preview.base_branch,
                    title=preview.title,
                    files=list(preview.files),
                    dry_run=True,
                )
            except (WorkloadValidationError, GitHubChangeError, ValueError) as exc:
                raise HTTPException(
                    status_code=422, detail=str(exc)
                ) from exc

        return ApplicationResponse(
            application=request.name,
            domain=request.domain,
            environment=request.environment,
            policy=policy,
            dry_run=True,
            status="preview",
            namespace=namespace,
            proposed_registry_path=proposed_registry_path,
            gitops_app_name=gitops_app_name,
            pull_request=pr_preview,
        )

    # Repository creation.
    repository_url = None
    if request.create_repository:
        try:
            created = RepositoryFactory(github).create_repository(
                name=request.name,
                description=request.description,
                private=True,
            )
            repository_url = created.url
        except RepositoryFactoryError as exc:
            raise HTTPException(
                status_code=502, detail=str(exc)
            ) from exc

    # Platform PR creation.
    pull_request_response = None
    partial_failure_reason = None

    if request.create_platform_pr:
        try:
            spec = WorkloadSpec(
                name=request.name,
                domain=request.domain,
                environment=request.environment,
                size=request.size.value,
                namespace_mode=request.namespace_mode.value,
                image=request.image,
                port=request.port,
                startup_path=request.health.startup_path,
                readiness_path=request.health.readiness_path,
                liveness_path=request.health.liveness_path,
            )
            changes = assembler.build(spec)
            preview = github.prepare_pull_request(
                workload_name=spec.name,
                domain=spec.domain,
                environment=spec.environment,
                changes=changes,
            )
            created_pr = github.create_pull_request(preview, changes)
            pull_request_response = PullRequestPreviewResponse(
                repository=github.repository,
                branch=preview.branch,
                base_branch=preview.base_branch,
                title=preview.title,
                files=list(preview.files),
                dry_run=False,
                number=created_pr.number,
                url=created_pr.url,
            )
        except (WorkloadValidationError, GitHubChangeError, ValueError) as exc:
            if repository_url:
                # Repository was created but PR failed: partial failure.
                partial_failure_reason = str(exc)
            else:
                raise HTTPException(
                    status_code=422, detail=str(exc)
                ) from exc

    # Determine final status.
    if partial_failure_reason:
        status = "partial_failure"
    elif repository_url and pull_request_response:
        status = "fully_onboarded"
    elif repository_url:
        status = "repository_created"
    elif pull_request_response:
        status = "platform_pr_created"
    else:
        status = "preview"

    dry_run = not (bool(repository_url) or bool(pull_request_response))

    return ApplicationResponse(
        application=request.name,
        domain=request.domain,
        environment=request.environment,
        policy=policy,
        dry_run=dry_run,
        status=status,
        namespace=namespace,
        proposed_registry_path=proposed_registry_path,
        gitops_app_name=gitops_app_name,
        repository_url=repository_url,
        pull_request=pull_request_response,
        partial_failure_reason=partial_failure_reason,
    )