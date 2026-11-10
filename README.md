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

## Developer Experience — Example Application Request

The following example demonstrates the intended end-to-end developer experience using the SOG Self-Service Developer Platform.

### Scenario

A developer from the Commerce team wants to create a new Python FastAPI application called `catalog-api`.

The developer does not want to manually:

- Create a GitHub repository.
- Configure GitHub Actions.
- Write a Dockerfile.
- Provision Kubernetes resources.
- Configure network policies.
- Set up monitoring.
- Configure Argo CD.
- Manage deployment manifests.

Instead, the developer submits an application request to the platform.

### Step 1 — Developer Submits a Request

**Future AI Chatbot Experience:**

> I want to create a Python FastAPI application called catalog-api for the Commerce team.
>
> Deploy it to the development environment using a small workload size.
>
> The application should only be accessible internally.
>
> Configure CI/CD with automated testing, security scanning, and Docker image builds.
>
> Enable application monitoring and logging.
>
> I want the application to deploy automatically whenever changes are merged into the main branch.

**MVP Platform API Experience:**

The same request can be submitted as structured JSON.

```json
{
  "name": "catalog-api",
  "domain": "commerce",
  "environment": "dev",
  "size": "small",
  "namespace_mode": "dedicated",
  "exposure": "internal",
  "language": "python",
  "framework": "fastapi",
  "port": 8080,
  "repository": {
    "create": true,
    "visibility": "private"
  },
  "cicd": {
    "enabled": true,
    "unit_tests": true,
    "security_scanning": true,
    "build_container": true,
    "push_to_acr": true,
    "auto_deploy": true
  },
  "observability": {
    "metrics": true,
    "logging": true
  }
}
```

> **Note:** This is the target application onboarding contract, not the current implemented API schema. Repository provisioning, CI/CD configuration, and observability options will be introduced incrementally.

### Step 2 — Platform Validates the Request

The Platform API:

1. Authenticates the developer using Microsoft Entra ID.
2. Resolves the developer's organizational identity and group membership.
3. Verifies authorization to create applications in the Commerce domain.
4. Validates workload specifications.
5. Evaluates organizational policies using OPA.
6. Checks for duplicate application names.
7. Determines whether additional approval is required.

If validation fails, the platform rejects the request and returns the reason.

### Step 3 — Platform Provisions the Application Repository

After authorization, the Repository Factory creates a private GitHub repository from an approved FastAPI Golden Path template.

**Example Generated Repository:**

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

The repository includes:

- A working FastAPI starter application.
- Health and readiness endpoints.
- Unit tests.
- Docker container configuration.
- GitHub Actions workflow.
- Application documentation.

### Step 4 — Platform Generates Infrastructure Configuration

The Infrastructure and GitOps factories generate:

- Terraform workload registration.
- Kubernetes namespace configuration.
- Kubernetes Deployment.
- Kubernetes Service.
- Kubernetes ServiceAccount.
- NetworkPolicy.
- ServiceMonitor.
- Argo CD Application registration.

**Example Kubernetes Namespace:**

```text
sog-dev-commerce-catalog-api
```

All generated infrastructure configuration is managed through the platform's GitOps repository.

### Step 5 — Developer Receives the Application Repository

The platform returns the repository URL and provisioning status.

**Example Target Response:**

```json
{
  "application": "catalog-api",
  "domain": "commerce",
  "environment": "dev",
  "status": "ready",
  "repository": {
    "name": "catalog-api",
    "url": "https://github.com/marksog/catalog-api"
  },
  "deployment": {
    "namespace": "sog-dev-commerce-catalog-api",
    "status": "configured"
  },
  "cicd": {
    "status": "configured"
  },
  "observability": {
    "status": "configured"
  }
}
```

> **Note:** This is an illustrative target response. The repository URL is an example and does not imply that the repository already exists. Actual status values must reflect completed provisioning operations.

### Step 6 — Developer Writes Application Code

The developer clones the generated repository and starts implementing business functionality.

```bash
git clone <generated-repository-url>

cd catalog-api
```

After making changes:

```bash
git add .

git commit -m "feat: implement product catalog endpoint"

git push origin main
```

### Step 7 — GitHub Actions Builds and Publishes the Application

The generated GitHub Actions pipeline executes:

```text
Developer Push
      |
      v
Run Unit Tests
      |
      v
Security Scanning
      |
      v
Build Docker Image
      |
      v
Authenticate to Azure via OIDC
      |
      v
Push Image to Azure Container Registry
      |
      v
Update GitOps Image Reference
      |
      v
Argo CD Synchronization
      |
      v
Deploy Application to AKS
```

For the MVP, successful changes to the main branch can trigger automated development deployment.

Production deployments will require additional approval controls.

### Step 8 — Application Becomes Available

After successful deployment:

- The application runs in AKS.
- Kubernetes health probes verify application health.
- Network policies control application connectivity.
- Prometheus collects application metrics.
- Grafana provides monitoring dashboards.
- Application logs are available through the platform's logging infrastructure.

### Expected Developer Experience

**Developer responsibility:**

Write application code, tests, and business logic.

**Platform responsibility:**

Provide the repository, CI/CD, infrastructure configuration, deployment automation, security guardrails, and observability.

### Future Agentic AI Experience

Once the core platform is functional, developers will be able to interact with the platform through an AI assistant.

Example:

**Developer:**
> Create a FastAPI service called catalog-api for Commerce.

**AI Agent:**
> Which environment should I use?

**Developer:**
> Development. Keep it internal and enable monitoring.

**AI Agent:**
> I will request a small FastAPI workload in the Commerce domain with internal networking, CI/CD, and monitoring. Would you like me to submit this request?

**Developer:**
> Yes.

**AI Agent:**
> Your request has been submitted to the Platform API. I will check its provisioning status.

The agent uses approved platform tools such as:

```python
create_application(...)
get_application_status(...)
get_deployment_status(...)
request_promotion(...)
```

The agent does not directly create Azure resources, modify Kubernetes clusters, or bypass organizational policies.

All infrastructure operations remain controlled by the Platform API.

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