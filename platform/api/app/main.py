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

from fastapi import FastAPI, HTTPException

from app.models import (
    PolicyDecision,
    PullRequestPreviewResponse,
    WorkloadRequest,
    WorkloadResponse,
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
# Workload onboarding
# --------------------------------------------------

@app.post(
    "/v1/workloads",
    response_model=WorkloadResponse,
)
def create_workload(request: WorkloadRequest):

    # LOCAL DEVELOPMENT ONLY.
    # This identity must be replaced with verified OIDC
    # authentication before enabling GitHub writes.
    identity = {
        "id": "local-commerce-developer",
        "groups": ["commerce-developers"],
    }

    # Step 1: Evaluate organizational policy.
    try:
        decision = evaluate_policy(
            workload=request.model_dump(mode="json"),
            identity=identity,
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
            dry_run=preview.dry_run,
        ),
    )