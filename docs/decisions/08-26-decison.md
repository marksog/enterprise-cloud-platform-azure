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