# ADR-0001: Adopt a Self-Service Internal Developer Platform with Guardrails

## Status

Accepted

---

# Context

As the organization grows, multiple engineering teams require cloud infrastructure, application hosting, networking, databases, Kubernetes clusters, identity, storage, observability, and deployment pipelines.

Traditionally, these resources have been provisioned either through manual requests to a central infrastructure team or directly by application teams with broad cloud permissions.

Both approaches create significant operational challenges.

When infrastructure is created independently by multiple teams, standards begin to diverge. Naming conventions become inconsistent, networking architectures differ between teams, security controls are implemented unevenly, monitoring varies across workloads, and cost attribution becomes increasingly difficult.

As the platform continues to grow, these inconsistencies lead to:

- Increased operational complexity
- Configuration drift
- Difficult incident response
- Poor visibility into infrastructure ownership
- Inconsistent security posture
- Difficult governance and auditing
- Reduced ability to scale engineering teams
- Increased cognitive load on application engineers

Conversely, requiring every infrastructure request to be fulfilled through a centralized platform team introduces a different set of problems:

- Long delivery times
- Infrastructure bottlenecks
- Reduced developer autonomy
- Poor engineering velocity
- Platform team becoming a scaling constraint

The organization requires an operating model that enables engineering teams to move quickly while maintaining enterprise standards for security, networking, governance, observability, and cost management.

---

# Decision

We will build and adopt an **Internal Developer Platform (IDP)** that provides self-service infrastructure capabilities through standardized golden paths operating within centrally governed guardrails.

Application teams will consume platform capabilities through supported interfaces such as:

- Developer Portal
- CLI
- REST API
- Git-based workflows

Application engineers will interact with platform capabilities rather than directly provisioning cloud infrastructure.

The platform will abstract infrastructure complexity while automatically enforcing organizational standards.

The platform will provide approved defaults for:

- Networking
- Identity
- Security
- Observability
- Logging
- Naming conventions
- Tagging
- Cost attribution
- CI/CD
- Workload deployment
- Operational standards

Developers will request capabilities instead of infrastructure.

For example, instead of requesting:

> "Create a VNet, NSGs, Route Tables, Key Vault, Monitoring, AKS namespace..."

they simply request:

> "Create a Production API."

The platform translates developer intent into standardized infrastructure.

Where a workload cannot use a supported golden path, a governed exception process will be used.

Exceptions must be:

- Justified
- Reviewed
- Auditable
- Periodically re-evaluated

---

# Alternatives Considered

## Option 1 – Centralized Ticket-Based Infrastructure

### Description

Application teams submit infrastructure requests to a centralized infrastructure or platform team.

### Benefits

- Central visibility
- Strong governance
- Easier auditing
- Infrastructure reviewed before deployment

### Drawbacks

- Platform team becomes a delivery bottleneck
- Long lead times
- Reduced developer autonomy
- Slower business delivery
- Difficult to scale as engineering teams grow
- Encourages shadow infrastructure when developers seek faster alternatives

### Decision

Rejected.

While governance is strong, the operational overhead and reduced engineering velocity make this approach unsuitable for a large enterprise platform.

---

## Option 2 – Unrestricted Cloud Access for Application Teams

### Description

Each engineering team provisions and manages its own Azure infrastructure.

### Benefits

- Maximum developer autonomy
- Fast infrastructure provisioning
- No dependency on platform engineers

### Drawbacks

- Inconsistent architecture
- Inconsistent networking
- Inconsistent security implementation
- Configuration drift
- Difficult governance
- Difficult auditing
- Increased blast radius
- Poor cost visibility
- Operational complexity
- Difficult incident response
- Increased cognitive load for application engineers

### Decision

Rejected.

Although developer autonomy is high, unrestricted infrastructure ownership introduces unacceptable operational, governance, and security risks.

---

## Option 3 – Self-Service Platform with Guardrails

### Description

Application teams consume standardized platform capabilities through self-service workflows while enterprise guardrails enforce organizational standards automatically.

### Benefits

- High developer autonomy
- Consistent infrastructure
- Enterprise governance
- Standardized security
- Reduced cognitive load
- Repeatable deployments
- Improved operational excellence
- Scalable engineering model

### Drawbacks

- Requires investment in platform engineering
- Platform becomes an internal product requiring ongoing maintenance
- Requires versioning, documentation, support, and lifecycle management

### Decision

Accepted.

This approach provides the best balance between developer experience, governance, operational excellence, and organizational scalability.

---

# Consequences

## Positive

The organization gains:

- Standardized infrastructure
- Consistent networking
- Consistent security posture
- Reduced configuration drift
- Faster developer onboarding
- Lower cognitive load
- Repeatable deployments
- Easier troubleshooting
- Better observability
- Improved cost attribution
- Reduced operational risk
- Scalable engineering practices

Application engineers focus on delivering business value instead of infrastructure implementation.

---

## Negative

The Platform Engineering team now owns an internal product rather than a collection of infrastructure scripts.

Responsibilities include:

- Platform lifecycle management
- Golden path evolution
- Documentation
- API versioning
- Developer experience
- Operational support
- Incident response
- Backward compatibility
- Governance implementation
- Platform roadmap

---

# Architectural Principles Established

This decision establishes the following principles for the platform.

## Principle 1 – Guardrails over Gates

Governance should be implemented through automation rather than manual approval whenever possible.

---

## Principle 2 – Secure Path is the Easy Path

The easiest way to provision infrastructure should also be the most secure and compliant.

---

## Principle 3 – Developers Consume Capabilities, Not Infrastructure

Application teams request platform capabilities rather than assembling cloud infrastructure.

---

## Principle 4 – Reduce Cognitive Load

Developers should understand the platform, but they should not require deep knowledge of the underlying cloud implementation to deliver business value.

---

## Principle 5 – Least Privilege by Default

Application teams receive only the permissions and capabilities required for their workloads.

---

## Principle 6 – Opinionated but Extensible

Golden paths should provide standardized defaults while supporting governed exceptions where legitimate business requirements exist.

---

## Principle 7 – Governance Proportional to Risk

Security and operational controls should reflect workload criticality rather than applying identical controls everywhere.

---

## Principle 8 – Platform as a Product

The Internal Developer Platform is a product with users, documentation, support, versioning, operational responsibilities, and continuous improvement.

---

# Principal Engineering Notes

This decision intentionally prioritizes long-term organizational scalability over short-term implementation simplicity.

The platform introduces additional engineering investment but significantly reduces operational complexity as the organization grows.

This ADR assumes:

- Multiple engineering teams
- Shared cloud platform
- Enterprise governance requirements
- Need for self-service capabilities
- Long-term platform ownership

This decision should be revisited if:

- Organizational scale changes significantly
- Regulatory requirements change
- Platform adoption becomes low
- New platform capabilities fundamentally change the operating model