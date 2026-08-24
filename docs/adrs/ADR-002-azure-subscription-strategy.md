# ADR-0003: Enterprise Subscription Strategy

## Status

Accepted

---

# Depends On

- ADR-0001 – Adopt a Self-Service Internal Developer Platform with Guardrails
- ADR-0002 – Adopt Azure Landing Zone Governance Hierarchy

---

# Context

The Azure platform will support multiple business units, engineering teams, internal applications, customer-facing services, regulated workloads, shared platform capabilities, and future organizational growth.

As the organization expands, workloads will differ significantly in:

- Governance requirements
- Security posture
- Operational ownership
- Lifecycle
- Financial accountability
- Compliance obligations
- Deployment cadence
- Disaster recovery requirements

Treating Azure subscriptions merely as billing containers or logical folders would create weak governance boundaries and increase operational complexity.

Conversely, creating subscriptions without a clear architectural principle leads to inconsistent designs where subscriptions reflect organizational charts, technology stacks, or temporary business structures rather than stable operating models.

The platform therefore requires a repeatable strategy for deciding:

- When a new subscription should be created.
- Which workloads belong together.
- Which workloads must remain isolated.
- How subscriptions should evolve as the organization grows.

This strategy must remain valid regardless of future cloud services or organizational changes.

---

# Decision

Azure subscriptions will be treated as **enterprise governance and operational boundaries**, not simply as billing containers.

A workload belongs in a subscription when it shares a common:

- Governance model
- Operational lifecycle
- Ownership model
- Security posture
- Financial accountability
- Operational characteristics

Subscriptions are intentionally designed to minimize shared operational risk while maximizing consistency within each operational domain.

The objective is to ensure that workloads requiring different governance, ownership, or operational practices are not forced into the same subscription.

The Internal Developer Platform will provision resources into the appropriate subscription based on workload classification rather than allowing application teams to choose subscription placement.

---

# Subscription Design Principles

## Principle 1 – Governance First

Subscription boundaries are determined by governance requirements before technology or organizational structure.

---

## Principle 2 – Shared Operating Model

Resources belong together only when they share:

- Governance
- Ownership
- Lifecycle
- Security controls
- Operational procedures
- Financial accountability

---

## Principle 3 – Minimize Blast Radius

Operational failures, permission mistakes, quota exhaustion, or configuration errors should affect the smallest reasonable portion of the platform.

---

## Principle 4 – Organizational Evolution

Subscription strategy should evolve as the organization's operating model evolves.

A smaller organization may operate multiple platform capabilities within a single Platform subscription.

As ownership, operational responsibilities, and governance mature, those capabilities may be separated into dedicated subscriptions without changing the overall architecture.

---

## Principle 5 – Platform Determines Placement

Application teams request platform capabilities.

The Internal Developer Platform determines the correct subscription based on organizational standards.

Subscription selection is an implementation detail of the platform rather than a developer decision.

---

# Initial Subscription Strategy

The platform initially adopts the following subscription model.

## Platform

Responsible for shared enterprise capabilities.

Initially contains:

- Connectivity
- Identity
- Shared Services
- Observability
- Platform Automation

Future organizational growth may separate these into dedicated subscriptions as ownership and operational models diverge.

---

## Regulated Production

Contains workloads requiring elevated governance, compliance, security, auditing, or regulatory controls.

Examples:

- Payments
- Payroll
- Financial systems
- Customer data platforms

---

## Standard Production

Contains production workloads operating under the organization's standard governance model.

Examples:

- Public APIs
- Marketing platforms
- Internal business applications

---

## Regulated Non-Production

Development, QA, and testing environments supporting regulated production systems.

Although non-production, these workloads continue to inherit additional governance appropriate to their production counterparts.

---

## Standard Non-Production

Development and testing environments for standard production workloads.

---

## Sandbox

Developer experimentation.

Characteristics include:

- Limited permissions
- Budget controls
- Automatic expiration
- No production data
- Relaxed governance compared to production

---

# Alternatives Considered

## Option 1 – Single Enterprise Subscription

### Benefits

- Simple initial deployment
- Minimal management overhead

### Drawbacks

- Large blast radius
- Poor governance separation
- Difficult ownership
- Weak cost attribution
- Subscription limits become organizational limits
- Difficult scaling

### Decision

Rejected.

---

## Option 2 – Subscription Per Application

### Benefits

- Strong application isolation
- Clear ownership

### Drawbacks

- Large subscription count
- Increased operational overhead
- Difficult governance management
- Unnecessary fragmentation

### Decision

Rejected as the default strategy.

Large enterprise applications may eventually justify dedicated subscriptions, but this is not the primary organizational model.

---

## Option 3 – Organize by Technology

Examples:

- Networking
- AKS
- SQL
- Storage

### Benefits

- Similar technologies grouped together

### Drawbacks

- Does not align with ownership
- Does not align with operational lifecycle
- Weak governance boundaries
- Poor workload cohesion

### Decision

Rejected.

Technology is not the primary architectural boundary.

---

## Option 4 – Organize by Operating Model

Subscriptions group workloads sharing governance, ownership, lifecycle, operational practices, security requirements, and financial accountability.

### Benefits

- Predictable governance
- Consistent operations
- Better scalability
- Strong ownership
- Reduced blast radius
- Easier automation
- Clear subscription purpose

### Decision

Accepted.

---

# Consequences

## Positive

- Consistent governance
- Clear ownership
- Better cost attribution
- Improved operational excellence
- Easier incident response
- Predictable automation
- Reduced blast radius
- Simplified onboarding
- Future organizational scalability

---

## Negative

- Subscription placement requires architectural thinking.
- The Platform Team must maintain subscription standards.
- Periodic reviews are required as the organization evolves.
- Subscription topology is expected to change over time.

---

# Principal Engineering Notes

A subscription is **not** a billing construct.

It is an operational boundary.

Subscription design should mirror how the organization operates rather than how Azure services are categorized.

As organizational ownership changes, subscription boundaries should evolve accordingly.

The goal is not to minimize or maximize the number of subscriptions.

The goal is to ensure that every subscription has a clear architectural purpose.

---

# Review Triggers

This ADR should be reviewed when:

- Organizational ownership changes.
- New business units are acquired.
- Compliance requirements change.
- Operational teams are reorganized.
- Platform capabilities significantly expand.
- Subscription governance no longer reflects the organization's operating model.