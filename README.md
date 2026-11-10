## Platform Vision: Self-Service Developer Platform

The SOG Enterprise Cloud Platform is a self-service Internal Developer Platform (IDP) designed to simplify application onboarding, infrastructure provisioning, CI/CD, deployment, and observability.

The goal is to enable developers to request an application environment and receive a ready-to-use GitHub repository with automated deployment capabilities.

The platform follows a **policy-driven, GitOps-based architecture**.

AI will eventually provide a conversational interface to the platform, but all provisioning and deployment operations will remain controlled by the Platform API and its security guardrails.

---

## Target Platform Architecture

```text
                    APPLICATION DEVELOPER
                             |
                             v
                   SELF-SERVICE INTERFACE
                    (API / Future Portal)
                             |
                             v
                    PLATFORM CONTROL PLANE
                       Python / FastAPI
                             |
              +--------------+--------------+
              |              |              |
              v              v              v
         VALIDATION      POLICY ENGINE    APPROVALS
              |              |              |
              +--------------+--------------+
                             |
                             v
                     PLATFORM ORCHESTRATOR
                             |
        +--------------------+--------------------+
        |                    |                    |
        v                    v                    v
   REPOSITORY            INFRASTRUCTURE       GITOPS
   FACTORY               FACTORY              FACTORY
        |                    |                    |
        v                    v                    v
   GitHub Repository      Terraform           Kubernetes
   Application Template   Azure Resources     Manifests
   GitHub Actions         Identity/RBAC       NetworkPolicy
   Dockerfile             Namespace           ServiceMonitor
   Unit Tests             Secrets Access      Argo CD App
        |                    |                    |
        +--------------------+--------------------+
                             |
                             v
                     DEVELOPER RECEIVES
                   READY-TO-USE REPOSITORY
                             |
                             v
                     DEVELOPER WRITES CODE
                             |
                             v
                         GIT PUSH
                             |
                             v
                      GITHUB ACTIONS
                    Test / Scan / Build
                             |
                             v
                    AZURE CONTAINER REGISTRY
                             |
                             v
                    GITOPS IMAGE PROMOTION
                             |
                             v
                          ARGO CD
                             |
                             v
                         AZURE AKS
                             |
                             v
                    RUNNING APPLICATION
                             |
                             v
                    OBSERVABILITY PLATFORM
                  Prometheus / Grafana / Logs
```

---

## Minimum Viable Platform (MVP)

The first objective is to deliver a thin but functional self-service developer platform.

We prioritize completing the developer journey over implementing every enterprise feature.

### MVP Success Criteria

A developer should be able to:

1. Submit an application request to the Platform API.
2. Have the request validated against organizational policies.
3. Receive a GitHub repository generated from an approved application template.
4. Write application code and push changes.
5. Trigger GitHub Actions automatically.
6. Run unit tests and baseline security scans.
7. Build and publish a container image to Azure Container Registry.
8. Promote the image through GitOps.
9. Deploy the application to Azure Kubernetes Service using Argo CD.
10. Access baseline application metrics and logs.

**MVP Definition of Done:**

A developer can request a FastAPI application, receive a usable repository, push code, and see the application deployed to AKS without manually creating Kubernetes manifests or configuring CI/CD.

---

## Platform Development Roadmap

### Phase 1 — Platform Foundation

**Status: Completed**

- [x] Establish Azure enterprise infrastructure.
- [x] Configure Terraform infrastructure management.
- [x] Deploy Azure Kubernetes Service (AKS).
- [x] Configure Azure Container Registry (ACR).
- [x] Establish GitOps using Argo CD.
- [x] Configure baseline security and networking.
- [x] Deploy Prometheus and Grafana.
- [x] Establish Platform API authentication and policy validation.

### Phase 2 — Workload Generation

**Status: Completed for MVP**

- [x] Define workload specifications.
- [x] Validate workload requests.
- [x] Generate Terraform workload registration.
- [x] Generate Kubernetes Deployment and Service.
- [x] Generate ServiceAccount.
- [x] Generate NetworkPolicy.
- [x] Generate ServiceMonitor.
- [x] Generate Argo CD Application registration.
- [x] Generate GitOps configuration changes.
- [x] Support GitHub pull request creation.
- [x] Validate generated Terraform and Kubernetes configuration.
- [x] Demonstrate successful application deployment (`inventory-api`).

### Phase 3 — GitHub Repository Factory

**Status: In Progress**

**Branch:** `feat/application-repository-factory`

- [ ] Create application repositories through the GitHub API.
- [ ] Generate repositories from approved Golden Path templates.
- [ ] Support a Python FastAPI starter application.
- [ ] Include Dockerfile.
- [ ] Include application unit tests.
- [ ] Include application README.
- [ ] Include GitHub Actions workflow templates.
- [ ] Return repository information to the developer.
- [ ] Preserve dry-run and authorization controls.

### Phase 4 — CI/CD Factory

**Status: Planned**

- [ ] Generate GitHub Actions CI/CD workflows.
- [ ] Run application unit tests.
- [ ] Perform baseline dependency and container security scans.
- [ ] Build Docker images.
- [ ] Configure Azure authentication using OIDC federation.
- [ ] Push images to Azure Container Registry.
- [ ] Publish immutable image references.

### Phase 5 — Image Promotion and GitOps Deployment

**Status: Planned**

- [ ] Connect successful CI builds to GitOps updates.
- [ ] Update application image references automatically.
- [ ] Support controlled GitOps pull requests.
- [ ] Trigger Argo CD synchronization.
- [ ] Verify application deployment to AKS.
- [ ] Support basic deployment rollback.

### Phase 6 — Multi-Environment Support

**Status: Planned**

- [ ] Define development environment configuration.
- [ ] Define staging environment configuration.
- [ ] Define production environment configuration.
- [ ] Support environment-specific application settings.
- [ ] Introduce approval gates for production.
- [ ] Establish a basic image promotion strategy.

**MVP Scope:** Fully demonstrate development deployment. Staging and production may initially use configuration placeholders.

### Phase 7 — Observability by Default

**Status: Partially Implemented**

- [x] Establish Prometheus and Grafana infrastructure.
- [x] Generate ServiceMonitor resources.
- [ ] Verify automatic application metrics scraping.
- [ ] Standardize structured application logging.
- [ ] Generate baseline dashboard templates.
- [ ] Define basic application alert rules.
- [ ] Provide application observability documentation.

### Phase 8 — Agentic AI Integration

**Status: Future**

The AI layer will be developed separately and integrated after the core platform workflow is functional.

The AI agent will operate as a developer-facing conversational interface.

It will interpret developer requests and invoke approved Platform API operations.

**The AI agent will not directly provision cloud infrastructure.**

```text
                  DEVELOPER
                      |
                      v
                 AI CHATBOT
                      |
                      v
                  AI AGENT
                      |
          +-----------+-----------+
          |                       |
          v                       v
    INTENT INTERPRETATION    PLATFORM KNOWLEDGE
          |                       |
          v                       v
    STRUCTURED REQUEST       DOCUMENTATION
          |                  SERVICE CATALOG
          |                  PLATFORM POLICIES
          |
          v
      PLATFORM API
          |
          v
    AUTHORIZATION + POLICY
          |
          v
    PLATFORM ORCHESTRATOR
          |
          v
    APPROVED PLATFORM OPERATIONS
          |
          v
    GITHUB / AZURE / GITOPS
```

#### Planned Agent Capabilities

- [ ] Interpret natural-language developer requests.
- [ ] Convert requests into structured workload specifications.
- [ ] Query the platform service catalog.
- [ ] Create application onboarding requests.
- [ ] Retrieve application provisioning status.
- [ ] Retrieve deployment status.
- [ ] Explain deployment failures.
- [ ] Request environment promotions.
- [ ] Integrate platform documentation through retrieval.
- [ ] Support human approval for sensitive operations.
- [ ] Maintain auditability of agent-initiated requests.

### Phase 9 — Future Enterprise Enhancements

**Status: Deferred**

- [ ] Developer self-service web portal.
- [ ] Additional application language templates.
- [ ] Automated database provisioning.
- [ ] Advanced secrets management workflows.
- [ ] Advanced SLO and reliability management.
- [ ] Cost optimization and chargeback.
- [ ] Automated incident remediation.
- [ ] Multi-cloud workload provisioning.
- [ ] Advanced platform analytics.

---

## Engineering Principles

The platform follows these development principles:

1. **Build → Validate → Integrate → Move On.**
2. Prioritize working end-to-end functionality over premature optimization.
3. Reuse existing platform components before introducing new abstractions.
4. Keep infrastructure provisioning behind deterministic policy and authorization controls.
5. Use GitOps as the source of truth for Kubernetes deployments.
6. Treat security and auditability as foundational requirements.
7. Document technical debt without allowing noncritical improvements to block MVP delivery.
8. Introduce advanced capabilities only when the core developer workflow is operational.

---

## Current Development Focus

**Milestone:** GitHub Repository Factory

**Branch:** `feat/application-repository-factory`

**Immediate Goal:**

Extend the existing Platform API to create a GitHub repository from a standard FastAPI Golden Path template.

The generated repository should contain:

```text
catalog-api/
├── app/
│   ├── __init__.py
│   └── main.py
├── tests/
│   └── test_health.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

**Acceptance Criteria:**

- Developer submits an authorized application request.
- Platform generates a repository from the approved template.
- Repository includes starter application code and CI/CD workflow.
- Platform returns the GitHub repository URL.
- Existing GitOps and workload generation capabilities remain functional.

**Next Milestone:** CI/CD Factory and Azure Container Registry integration.