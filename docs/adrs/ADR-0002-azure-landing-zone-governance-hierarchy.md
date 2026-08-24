# ADR-0002: Adopt Azure Landing Zone Governance Hierarchy

## Status

Proposed

## Depends On

ADR-0001: Adopt a Self-Service Internal Developer Platform with Guardrails

## Context

The Azure platform is expected to support multiple business units, engineering teams, production and non-production workloads, regulated applications, shared platform capabilities, centralized networking, identity services, security tooling, and future organizational growth.

A single Azure subscription would provide initial simplicity but would create excessive shared fate as the organization grows.

Unrelated workloads would share governance boundaries, permissions, quotas, operational responsibilities, cost structures, and lifecycle decisions. This would increase blast radius, complicate security and policy enforcement, weaken ownership boundaries, and make organizational scaling more difficult.

The platform therefore requires a hierarchy that allows governance to be applied consistently at broad organizational scopes while still allowing stricter or more specialized controls for workloads with different risk and operating requirements.

The hierarchy must support:

- Central governance
- Policy inheritance
- Security boundaries
- Separation of production and non-production concerns
- Regulated workload requirements
- Shared platform services
- Cost attribution
- Operational ownership
- Subscription-scale growth
- Future acquisitions and organizational change

## Decision

We will adopt an Azure Landing Zone governance hierarchy based on **shared governance and operating requirements** rather than technology type or organizational department alone.

Azure Management Groups will be used to organize subscriptions that require common policies, controls, security posture, and operational standards.

Subscriptions will act as meaningful operating and governance boundaries for workloads that share similar:

- Security requirements
- Policy requirements
- Ownership models
- Financial responsibility
- Operational lifecycle
- Networking requirements
- Resource quotas and limits
- Compliance obligations

Resource Groups will provide finer-grained management boundaries within subscriptions for resources that share a lifecycle, ownership model, operational responsibility, or access pattern.

The hierarchy will allow organization-wide controls to be applied at higher scopes while more restrictive or workload-specific controls are applied lower in the hierarchy.

Governance will be applied at the **highest appropriate scope where a requirement is universally valid**, while specialized requirements will be applied only where necessary.

## Initial Conceptual Hierarchy

```text
Azure Tenant
│
└── Organization
    │
    ├── Platform
    │   ├── Connectivity
    │   ├── Identity
    │   ├── Management
    │   └── Security
    │
    ├── Workloads
    │   ├── Regulated
    │   ├── Standard Production
    │   └── Non-Production
    │
    └── Sandbox
```

This hierarchy is intentionally conceptual.

The final Management Group and subscription topology will be refined as additional requirements are discovered.

## Alternatives Considered

### Option 1 – Single Azure Subscription

All production, non-production, shared platform, networking, security, and application workloads would exist in one subscription.

#### Benefits

- Simple initial setup
- Fewer subscriptions to manage
- Easier for a very small organization

#### Drawbacks

- Large blast radius
- Shared resource quotas
- Broad permission scopes
- Difficult ownership boundaries
- Complicated cost attribution
- Difficult policy specialization
- Increased operational coupling
- Poor separation between production and non-production
- Difficult lifecycle management
- Limited scalability as engineering teams grow

#### Decision

Rejected.

The approach optimizes for short-term simplicity but creates excessive shared fate and governance complexity at enterprise scale.

---

### Option 2 – Organize Subscriptions by Technology

Examples:

- AKS subscription
- Database subscription
- Storage subscription
- Networking subscription

#### Benefits

- Resources of similar technical types are grouped together
- Technology-specific teams may find ownership straightforward

#### Drawbacks

- Application workloads become distributed across multiple subscriptions
- Lifecycle management becomes fragmented
- Application ownership becomes difficult
- Failure and operational boundaries do not align with business workloads
- Cost attribution becomes harder
- Governance requirements are not necessarily determined by technology type

#### Decision

Rejected.

Technology should not define the primary enterprise governance boundary.

---

### Option 3 – Organize Primarily by Business Unit or Application Team

Examples:

- Payments
- Marketing
- HR
- Sales

#### Benefits

- Clear organizational ownership
- Cost attribution may be easier
- Teams have identifiable boundaries

#### Drawbacks

- A single business unit may contain production, development, regulated, and low-risk workloads
- Different workloads within the same department may require very different policies
- Organizational structures change frequently
- The hierarchy can become tightly coupled to the company's reporting structure

#### Decision

Rejected as the primary design principle.

Business ownership will influence subscription and resource organization, but governance requirements take precedence.

---

### Option 4 – Organize by Governance and Operating Model

Subscriptions are grouped according to common risk, security, policy, lifecycle, and operational requirements.

#### Benefits

- Supports policy inheritance
- Aligns governance with risk
- Reduces unnecessary controls
- Improves isolation
- Supports regulated workloads
- Enables centralized platform services
- Scales to large numbers of subscriptions
- Supports acquisitions and organizational change
- Provides clearer ownership and cost boundaries

#### Drawbacks

- Requires deliberate hierarchy design
- Requires ongoing governance ownership
- Incorrect classification can lead to over-governance or under-governance
- Subscription placement and policy inheritance must be carefully managed

#### Decision

Accepted.

This approach provides the strongest foundation for enterprise-scale governance while allowing workloads with materially different requirements to operate under appropriate controls.

## Consequences

### Positive

- Policies can be inherited rather than duplicated across subscriptions.
- Production and regulated workloads can receive stronger controls without imposing unnecessary restrictions everywhere.
- Shared platform capabilities can have separate ownership and operational models.
- Subscription-level failures, quotas, and permission mistakes have smaller blast radii.
- Cost ownership becomes clearer.
- The organization can add subscriptions without redesigning the entire governance model.
- Future acquisitions can be integrated into the hierarchy incrementally.
- Platform automation can target predictable governance boundaries.

### Negative

- The hierarchy itself becomes critical platform architecture and must be governed carefully.
- Management Group changes can affect many subscriptions simultaneously.
- Poorly designed policy inheritance can create large-scale outages or developer friction.
- Subscription topology must evolve as organizational and regulatory requirements change.
- Platform engineers must maintain documentation explaining why each boundary exists.

## Architectural Principles Established

### Principle 1 – Governance Drives Hierarchy

Management Groups and subscriptions will be structured around common governance and operating requirements.

### Principle 2 – Apply Controls at the Highest Appropriate Scope

Policies should be assigned high enough to ensure consistency, but not so high that workloads inherit unnecessary restrictions.

### Principle 3 – Governance is Proportional to Risk

Regulated and critical workloads may require stricter controls than standard or experimental workloads.

### Principle 4 – Minimize Shared Fate

Unrelated workloads should not unnecessarily share permission, quota, lifecycle, or operational failure boundaries.

### Principle 5 – Organizational Structure is Not Architecture

The Azure hierarchy should not blindly mirror the company's reporting structure.

### Principle 6 – Subscription Boundaries Are Intentional

Subscriptions are operating and governance boundaries, not merely containers for resources.

### Principle 7 – Resource Groups Represent Management Cohesion

Resources should be grouped together when they share meaningful lifecycle, ownership, operational, or access characteristics.

## Principal Engineering Notes

A Principal Engineer should support this decision because it creates a scalable governance model without requiring identical controls across all workloads.

The design deliberately balances centralized governance with decentralized workload ownership.

The most important tradeoff is added organizational complexity in exchange for stronger isolation, policy inheritance, ownership clarity, and long-term scalability.

This decision assumes:

- The organization will operate many Azure subscriptions.
- Workloads will have materially different risk profiles.
- Centralized governance will be required.
- Platform Engineering will own or coordinate the hierarchy.
- Policies and subscription placement will be automated wherever possible.

## Review Triggers

This decision should be revisited if:

- Regulatory requirements materially change.
- The organization undergoes significant restructuring.
- Acquisitions introduce new tenant or sovereignty requirements.
- Subscription count grows beyond the current operating model.
- Policy inheritance becomes excessively complex.
- Workloads repeatedly require exceptions to the existing hierarchy.
- Azure introduces a materially different governance model that better meets these requirements.