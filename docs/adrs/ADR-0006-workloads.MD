ADR-004 — Application Authentication Ownership

Decision: SOG will initially use application-managed service-to-service authentication, supported by platform-provided identity and security capabilities.

Rationale: Preserve application-team ownership while avoiding the operational complexity of introducing a service mesh at this stage.

Consequences: Application teams must implement and test authorization correctly. The platform team must provide approved libraries, documentation, identity integration, and security validation.