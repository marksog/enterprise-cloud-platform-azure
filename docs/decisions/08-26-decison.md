Implementation Decision 001

Platform Deployment Identity

Decision

Use a single enterprise workload identity named:

sog-platform-deployment

Reason

Identity represents the business capability rather than the CI/CD technology.

Future CI/CD systems may reuse the same identity.

# next decision
having several identities to separate duties.
sog-mg-deployment
sog-policy-deployment
sog-network-deployment
sog-identity-deployment
sog-platform-deployment
sog-aks-deployment
sog-app-deployment


DEC-0004

Title:
Version-Control Enterprise Platform Intent

Status:
Accepted

Date:
2026-08-26

Context

Terraform traditionally ignores terraform.tfvars because it frequently contains
environment-specific configuration, credentials, or other sensitive values.

For the Management Groups layer, the tfvars file contains the enterprise
governance hierarchy rather than secrets.

Examples include:

- Organization prefix
- Enterprise hierarchy
- Platform hierarchy
- Production hierarchy
- Sandbox hierarchy

These values represent platform architecture rather than runtime configuration.

Decision

Version-control the Management Groups intent configuration.

Update .gitignore to continue ignoring terraform.tfvars globally while explicitly
allowing:

terraform/management-groups/terraform.tfvars

Rationale

- Enterprise governance is part of platform architecture.
- Every engineer should review governance changes through Pull Requests.
- CI/CD requires the same organizational intent available locally.
- These values are not secrets.
- Keeping governance under version control improves reproducibility,
  documentation, and reviewability.

Consequences

Positive

- GitHub Actions can execute Terraform Plan without additional variable injection.
- Governance changes become part of normal code review.
- Platform intent remains reproducible.

Negative

- Future environment-specific values should not be added to this file.
- Secrets and environment-specific configuration remain excluded from Git.