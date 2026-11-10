# enterprise-cloud-platform-azure

## Azure Policy Governance

The platform applies an Enterprise Security Baseline at the `sog-enterprise`
Management Group.

Current controls:

- Public storage access denied
- Secure transfer required
- Minimum TLS 1.2
- Azure locations restricted to East US and East US 2
- Enterprise tags required: Environment, Owner, CostCenter

Policy architecture:

Definitions → Initiatives → Assignments → Exemptions

Microsoft built-in policies are preferred for standard controls. Custom
definitions are used only for organization-specific requirements.

Policy is deployed through GitHub Actions using workload identity federation,
separate plan/deployment identities, remote Terraform state, and a gated
production apply workflow.


Big picture 

                    APPLICATION DEVELOPER
                             |
                             |
                 SELF-SERVICE PLATFORM PORTAL
                             |
                  Natural Language / Form
                             |
                             v
                  AI PLATFORM ASSISTANT
                (Intent Interpretation)
                             |
                  "What do you want?"
                             |
                             v
                    PLATFORM CONTROL PLANE
                   (Python / FastAPI)
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
   PROVISIONING          PROVISIONING         GENERATION
        |                    |                    |
        v                    v                    v
   GitHub Repository       Terraform          Kubernetes
   Application Template    Azure Resources    Manifests
   GitHub Actions          Identity/RBAC       NetworkPolicy
   Dockerfile              Secrets Access     ServiceMonitor
   Tests                   Database           Argo CD App
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
                    Tests / Build / Scan
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