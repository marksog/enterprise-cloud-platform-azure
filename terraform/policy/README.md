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


1. Terraform modules are isolated; inputs and outputs cross module boundaries explicitly.

2. terraform_remote_state is a contract between independently managed stacks.

3. A wrong backend key can silently create an empty state, so state naming is architectural, not cosmetic.

4. OIDC authentication, RBAC authorization, and network access are three separate security gates.

5. Policy Definition = rule.
   Initiative = collection of rules.
   Assignment = where the rules apply.
   Exemption = controlled exception.

6. Built-in policy display names are less stable than immutable policy definition IDs.

7. AzureRM has scope-specific resources, such as
   azurerm_management_group_policy_set_definition.

8. Deny policies at an Enterprise Management Group have a large blast radius, so plan review and gated apply matter.