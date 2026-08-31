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