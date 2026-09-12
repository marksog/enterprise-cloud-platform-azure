# Connectivity Migration — September 2026

## Status

Completed

## Date

September 2026

## Scope

Migration of the Azure shared connectivity platform from the temporary student connectivity subscription to the paid Connectivity subscription.

---

# Executive Summary

The Azure platform's shared connectivity services were migrated from a temporary student subscription into the paid Connectivity subscription without rebuilding the existing Production and Non-Production spokes.

The migration moved centralized routing, NVA-based Internet egress, hub-and-spoke peering, and Private DNS ownership to the paid Connectivity subscription while preserving the existing workload networks.

The final topology uses:

- Paid hub VNet: `10.30.0.0/20`
- NVA private IP: `10.30.0.196`
- Production spoke: `10.10.0.0/20`
- Non-Production spoke: `10.20.0.0/20`
- Central Private DNS zone: `privatelink.vaultcore.azure.net`

The migration was intentionally staged.

Replacement infrastructure was built first, control-plane configuration was validated, real Production traffic was tested through the new NVA, centralized DNS was migrated, and only then was the old connectivity environment destroyed.

The migration also exposed several realistic platform-engineering failure modes involving:

- Azure resource-provider registration
- Terraform saved-plan staleness
- subnet addressing constraints
- active NIC allocations
- GitHub Actions OIDC federation
- Terraform state locking
- Azure Policy
- NSG transit rules
- cross-subscription RBAC
- Private DNS migration
- partial Terraform applies

Each failure was resolved by identifying the failing architectural boundary rather than bypassing the platform control.

---

# Why the Migration Was Required

The original shared hub was hosted in a student subscription.

That was acceptable during early platform development but was not an appropriate long-term ownership boundary for shared enterprise connectivity.

The goal was not simply to recreate resources in another subscription.

The migration needed to preserve the existing spoke networks while establishing a cleaner platform ownership model.

The major constraints were:

- Do not rebuild Production or Non-Production VNets.
- Do not change the spoke CIDRs.
- Preserve connectivity until the replacement path is proven.
- Keep Terraform ownership explicit.
- Continue using GitHub Actions OIDC rather than long-lived Azure credentials.
- Apply least-privilege RBAC across subscription boundaries.
- Validate the data plane, not just Azure resource status.
- Maintain Terraform state locking.
- Preserve a rollback path until the replacement architecture is validated.

---

# Starting Architecture

The original architecture used:

```text
Student Connectivity Subscription
|
+-- Hub VNet 10.0.0.0/20
|   |
|   +-- AzureFirewallSubnet
|   +-- AzureBastionSubnet
|   +-- GatewaySubnet
|   +-- shared-services-subnet
|   +-- nva-subnet
|
+-- Lab NVA networking
+-- Central Private DNS
+-- Hub/spoke peerings

Production Subscription
|
+-- VNet 10.10.0.0/20

Non-Production Subscription
|
+-- VNet 10.20.0.0/20
```

The Production and Non-Production spokes already contained the network structure the platform wanted to preserve.

---

# Target Architecture

The replacement design moved shared connectivity into the paid Connectivity subscription.

```text
                         Internet
                            |
                            v
                     NVA 10.30.0.196
                            |
                            v
                 Paid Hub 10.30.0.0/20
                    /               \
                   /                 \
                  v                   v
        Prod 10.10.0.0/20    NonProd 10.20.0.0/20
```

The paid Connectivity stack became responsible for:

- Hub VNet
- Hub subnets
- NVA
- NVA networking
- NVA NSG
- Hub-to-spoke peerings
- Spoke-to-hub peerings
- Centralized Private DNS

The Network stack retained responsibility for:

- Production VNet
- Non-Production VNet
- Spoke subnets
- NSGs
- Route tables
- Route-table associations
- Key Vaults
- Private Endpoints
- Spoke DNS VNet links

---

# Terraform Ownership Boundary

One of the goals of the migration was to establish explicit infrastructure ownership.

## Connectivity Stack

```text
terraform/connectivity/
```

Owns shared connectivity services.

Examples:

```text
Hub VNet
NVA
NVA NSG
Hub subnets
Peerings
Central Private DNS
```

## Network Stack

```text
terraform/network/
```

Owns workload-facing networking.

Examples:

```text
Production VNet
NonProd VNet
Spoke subnets
NSGs
Route tables
Private Endpoints
Key Vaults
DNS VNet links
```

The principle is:

> A resource has one authoritative Terraform owner.

Cross-stack dependencies are consumed through explicit outputs and remote state rather than duplicate ownership.

---

# Migration Strategy

The migration followed a build-before-destroy approach.

```text
Build replacement
      |
      v
Connect replacement
      |
      v
Validate control plane
      |
      v
Cut spoke routes to new NVA
      |
      v
Validate real workload traffic
      |
      v
Migrate Private DNS
      |
      v
Validate DNS records
      |
      v
Remove old connectivity path
```

The old environment remained available until the replacement path had been demonstrated to work.

This preserved a practical rollback option during the highest-risk stages.

---

# New Hub Addressing

The new paid hub uses:

```text
10.30.0.0/20
```

The NVA uses:

```text
10.30.0.196
```

The existing spoke CIDRs remained unchanged:

```text
Production:
10.10.0.0/20

Non-Production:
10.20.0.0/20
```

The migration therefore changed the shared transit infrastructure without readdressing the workload spokes.

---

# Route Cutover

Production and Non-Production default routes were changed to use the new NVA.

```text
0.0.0.0/0
     |
     v
VirtualAppliance
     |
     v
10.30.0.196
```

The route-table migration was deliberately separated from destruction of the old hub.

This allowed the new traffic path to be tested while the legacy infrastructure still existed.

---

# Runtime Validation

The spokes did not contain an existing workload suitable for end-to-end testing.

A temporary private Production VM was therefore created in the Production application subnet.

The VM had:

- no public IP
- a private address in the Production application subnet
- the Production route table
- the same network path a real workload would use

Its effective route confirmed:

```text
0.0.0.0/0
-> VirtualAppliance
-> 10.30.0.196
```

Azure Run Command was used to generate HTTPS traffic from the VM.

This avoided adding a public management path to the test workload.

---

# Packet Capture Validation

On the NVA, packet capture was performed with:

```bash
sudo tcpdump -ni any host 10.10.0.4
```

`tcpdump` was used as a passive observer.

It did not generate traffic.

The test was:

```text
Production VM
10.10.0.4
     |
     | HTTPS request
     v
Internet
```

while the NVA watched for traffic involving:

```text
10.10.0.4
```

The first test timed out.

No Production packets appeared on the NVA.

This was important because the Azure control plane looked healthy.

The following were already correct:

- route table
- effective route
- VNet peering
- NVA state
- Terraform deployment

Yet the data plane was still broken.

---

# Missing NVA Transit NSG Rule

Investigation showed that the NVA NSG permitted administrative SSH but did not permit spoke transit traffic to reach the NVA.

The packet therefore died before reaching the Linux operating system.

The NSG needed to allow traffic from:

```text
10.10.0.0/20
10.20.0.0/20
```

A spoke-transit rule was added.

The Linux NVA remained responsible for more granular forwarding policy.

This created layered enforcement:

```text
Spoke
  |
  v
Azure NSG
  |
  v
Linux NVA
  |
  v
iptables FORWARD
  |
  v
NAT
  |
  v
Internet
```

After the NSG rule was deployed, the same Production test was repeated.

This time `tcpdump` showed Production traffic traversing the NVA.

The TCP connection and return traffic were visible.

That validated:

```text
Production workload
      |
      v
Production UDR
      |
      v
Hub peering
      |
      v
NVA NSG
      |
      v
Linux forwarding
      |
      v
NAT / MASQUERADE
      |
      v
Internet
      |
      v
Return traffic
```

This became the decisive data-plane validation for the cutover.

---

# Control Plane vs Data Plane

One of the most important lessons from the migration was the difference between configuration health and service health.

Before the NSG fix:

```text
Terraform Apply      SUCCESS
VNet Peering         CONNECTED
UDR                   ACTIVE
Effective Route      CORRECT
NVA                   RUNNING
```

but:

```text
Actual workload traffic
FAILED
```

Therefore:

> A healthy control plane does not prove a healthy data plane.

Network migrations require actual traffic validation.

---

# Governance During Testing

The first attempt to create the temporary Production validation VM was rejected by Azure Policy because required enterprise tags were missing.

The missing requirement included:

```text
CostCenter
```

The policy was not disabled.

The test workload was changed to comply with the platform contract.

The temporary NIC and VM were created with the required tags.

This demonstrated that governance remained effective even during troubleshooting.

The principle followed was:

> Troubleshooting resources should comply with platform guardrails rather than bypass them.

---

# Azure Resource Provider Registration Failure

The new hub deployment initially failed because the paid subscription had not registered:

```text
Microsoft.Network
```

Azure returned:

```text
MissingSubscriptionRegistration
```

The resource provider was registered and deployment was retried.

This identified provider registration as a required subscription-bootstrap responsibility.

A mature landing-zone bootstrap process should ensure required Azure providers are registered before downstream infrastructure is deployed.

---

# Hub Address-Space Constraint

During the migration, Azure rejected an attempted subnet configuration because the subnet CIDR was outside the VNet address space.

The error demonstrated the dependency:

```text
VNet CIDR
   |
   v
Subnet CIDR
```

A subnet cannot exist outside its parent VNet's address space.

The hub addressing migration therefore required explicit sequencing rather than simply changing independent Terraform values.

---

# Active Allocation Preventing Subnet Mutation

Another attempted subnet change failed because the old NVA NIC still held an active allocation in the subnet.

Azure reported that the existing prefix could not be deleted while allocations remained.

The dependency chain was:

```text
VNet
 |
 v
Subnet
 |
 v
NIC
 |
 v
VM / workload
```

This reinforced the principle that infrastructure changes must respect the cloud-resource dependency graph.

Terraform configuration may express desired state, but Azure still enforces resource lifecycle dependencies.

---

# Terraform Saved Plan Became Stale

During the migration, a saved Terraform plan later failed with:

```text
Saved plan is stale
```

Terraform state had changed after the plan was generated.

The old plan was not reused.

Instead:

```text
State changed
     |
     v
Discard saved plan
     |
     v
Generate new plan
     |
     v
Review
     |
     v
Apply
```

The lesson was:

> A Terraform saved plan represents a specific state snapshot.

When state changes, the plan must be regenerated.

---

# Terraform State Lock Failure

An early Terraform workflow authenticated successfully but failed while acquiring the remote state lock.

The failure was caused by Azure Storage authorization.

The solution was not:

```text
terraform ... -lock=false
```

Instead, the required Azure RBAC was corrected.

Terraform state locking remained enabled throughout the platform workflow.

This preserved protection against concurrent state modifications.

---

# GitHub Actions OIDC

GitHub Actions authenticates to Azure using OpenID Connect workload identity federation.

The architecture avoids storing long-lived Azure client secrets in GitHub.

Conceptually:

```text
GitHub Actions
      |
      v
OIDC token
      |
      v
Microsoft Entra ID
      |
      v
Federated Identity Credential
      |
      v
Azure Service Principal
      |
      v
Terraform
```

---

# OIDC Federated Identity Failure

Initial workflows failed because Microsoft Entra ID could not find a federated identity matching the subject presented by GitHub.

Different GitHub execution contexts generated different subjects.

Examples included branch-based subjects:

```text
repo:<repository>:ref:refs/heads/main
```

and GitHub Environment subjects:

```text
repo:<repository>:environment:<environment-name>
```

The required federated credentials were configured for the workflow execution contexts actually used by the platform.

Authentication then succeeded without introducing stored Azure secrets.

The lesson was:

> OIDC trust is established against the token claims produced by the execution context, not merely against the repository name.

---

# Plan and Deploy Identity Separation

Terraform planning and deployment use separate identities.

The Plan identity primarily requires:

- state access
- resource refresh permissions
- cross-subscription read access
- enough Azure visibility to generate an accurate plan

The Deploy identity requires:

- approved infrastructure write permissions
- linked-resource permissions
- cross-subscription permissions required for deployment

This reduces unnecessary write access during pull-request validation.

---

# Private DNS Migration

The original Key Vault Private DNS zone was hosted in the student Connectivity subscription:

```text
privatelink.vaultcore.azure.net
```

DNS could not simply be destroyed during the hub cleanup because Production and Non-Production Private Endpoints depended on it.

The DNS migration therefore used a separate staged process.

---

# New Centralized DNS Zone

A replacement zone was created in the paid Connectivity subscription:

```text
privatelink.vaultcore.azure.net
```

The Connectivity Terraform stack became the authoritative owner.

The Connectivity stack exported the zone ID:

```hcl
output "key_vault_private_dns_zone_id" {
  description = "Resource ID of the centralized Key Vault Private DNS zone."
  value       = azurerm_private_dns_zone.key_vault.id
}
```

The Network stack consumed the value through:

```text
connectivity.tfstate
```

This created an explicit interface:

```text
Connectivity stack
       |
       | output
       v
connectivity.tfstate
       |
       | remote state
       v
Network stack
```

The complete Azure resource ID was not hardcoded into the Network configuration.

---

# DNS Consumer Migration

Production and Non-Production DNS VNet links were moved from the old zone to the new Connectivity-owned zone.

The Key Vault Private Endpoint DNS zone groups were also updated.

The target state became:

```text
Paid Connectivity Subscription
|
+-- privatelink.vaultcore.azure.net
      |
      +-- Paid Hub link
      +-- Production link
      +-- Non-Production link
```

Production and Non-Production Key Vault Private Endpoints now consume the centralized paid-connectivity DNS zone.

---

# Cross-Subscription DNS RBAC Failure

The first DNS cutover apply partially progressed and then failed.

Terraform successfully destroyed some old VNet links before Azure rejected creation of the new relationships.

The Network Deploy identity could modify the Private Endpoints but lacked permission on the Connectivity-owned Private DNS zone.

Azure required:

```text
Microsoft.Network/privateDnsZones/join/action
```

The identity was granted:

```text
Private DNS Zone Contributor
```

at the specific Private DNS zone scope.

Broad Contributor access over the Connectivity subscription was not required.

This followed least privilege.

---

# Partial Terraform Apply

The DNS failure demonstrated an important Terraform behavior.

Terraform apply is not an all-or-nothing database transaction.

The environment reached a state similar to:

```text
Old DNS links
     |
     v
Destroyed

New DNS links
     |
     v
Creation attempted

RBAC failure
     |
     v
Apply stops
```

Some changes had already occurred.

The recovery approach was:

1. Identify the real authorization failure.
2. Correct the minimum required RBAC.
3. Do not attempt to reuse the old saved plan.
4. Generate a fresh Terraform plan.
5. Refresh actual Azure state.
6. Allow Terraform to reconcile the partial state.
7. Apply forward.

Terraform successfully converged the environment.

The lesson was:

> After a partial apply, fix the underlying dependency and reconcile forward from actual state.

---

# Plan Identity DNS RBAC Failure

After the Deploy identity was fixed, a later Terraform plan failed while refreshing the new DNS VNet links.

The Network Plan identity lacked:

```text
Microsoft.Network/privateDnsZones/virtualNetworkLinks/read
```

on the Connectivity-owned DNS zone.

The Plan identity was granted:

```text
Private DNS Zone Contributor
```

at the DNS-zone scope.

Terraform could then refresh the cross-subscription resources and generate an accurate plan.

This demonstrated:

> Read-only planning still requires visibility into every resource represented in Terraform state.

---

# DNS Validation

Before deleting the old Private DNS zone, the new zone was queried.

Records existed for:

```text
sog-prod-kv
sog-nonprod-kv
```

This proved that the new Connectivity-owned DNS zone contained the required Private Endpoint records.

Only after this validation was the old DNS zone approved for destruction.

---

# Legacy Peering Cleanup

The old hub peerings were removed in a dedicated cleanup change.

The Terraform plan contained:

```text
0 to add
0 to change
4 to destroy
```

The four resources were only the old hub/spoke peering relationships.

This intentionally separated connectivity detachment from destruction of the underlying hub infrastructure.

---

# Legacy Infrastructure Cleanup

After the new routing and DNS paths were validated, the old student connectivity resources were removed.

The cleanup included:

- old hub VNet
- old hub subnets
- old NVA NIC
- old NVA public IP
- old Private DNS zone

The cleanup plan was reviewed to confirm that no Production or Non-Production workload resources were being destroyed.

---

# Final Resource Group Cleanup

The old connectivity resource group was intentionally retained until the resources inside it had been removed.

The final Terraform plan contained:

```text
Plan: 0 to add, 0 to change, 1 to destroy
```

The only resource was the empty legacy

 connectivity resource group.

After that resource group was destroyed, the original student-subscription connectivity environment was fully retired.

This final step confirmed that the migration had removed the platform's dependency on the temporary subscription.

---

# Final Architecture

The completed platform architecture is:

```text
Azure Platform
|
+-- Paid Connectivity Subscription
|   |
|   +-- Hub VNet
|   |     10.30.0.0/20
|   |
|   +-- Network Virtual Appliance
|   |     Private IP: 10.30.0.196
|   |
|   +-- NVA Network Security Group
|   |
|   +-- Hub-to-Production peering
|   +-- Production-to-Hub peering
|   |
|   +-- Hub-to-NonProd peering
|   +-- NonProd-to-Hub peering
|   |
|   +-- Central Private DNS
|         privatelink.vaultcore.azure.net
|
+-- Production Subscription
|   |
|   +-- VNet
|   |     10.10.0.0/20
|   |
|   +-- Application subnet
|   +-- Data subnet
|   +-- AKS subnet
|   +-- Private Endpoint subnet
|   |
|   +-- NSGs
|   |
|   +-- Route table
|   |     0.0.0.0/0
|   |        |
|   |        v
|   |     10.30.0.196
|   |
|   +-- Key Vault
|         |
|         +-- Private Endpoint
|
+-- Non-Production Subscription
    |
    +-- VNet
    |     10.20.0.0/20
    |
    +-- Application subnet
    +-- Data subnet
    +-- AKS subnet
    +-- Private Endpoint subnet
    |
    +-- NSGs
    |
    +-- Route table
    |     0.0.0.0/0
    |        |
    |        v
    |     10.30.0.196
    |
    +-- Key Vault
          |
          +-- Private Endpoint
```

The old student-subscription connectivity hub no longer exists.

---

# Final Traffic Path

Production Internet traffic follows:

```text
Production workload
10.10.x.x
      |
      v
Production subnet
      |
      v
Production route table
      |
      | 0.0.0.0/0
      v
Virtual Appliance
10.30.0.196
      |
      v
Paid Connectivity Hub
      |
      v
NVA NSG
      |
      v
Linux IP forwarding
      |
      v
iptables FORWARD
      |
      v
NAT / MASQUERADE
      |
      v
Internet
```

Non-Production follows the equivalent path from:

```text
10.20.0.0/20
```

---

# Final Private DNS Path

Private DNS resolution follows:

```text
Production / NonProd workload
           |
           v
Azure DNS resolution
           |
           v
privatelink.vaultcore.azure.net
           |
           v
Central DNS zone
Paid Connectivity Subscription
           |
           v
Private Endpoint A record
           |
           v
Key Vault private IP
```

The verified zone contains records for:

```text
sog-prod-kv
sog-nonprod-kv
```

---

# What Went Well

Several parts of the migration worked particularly well.

## Staged migration

The replacement environment was built before the original environment was removed.

This maintained a rollback path during high-risk stages.

## Existing spokes were preserved

Production and Non-Production VNets did not need to be rebuilt.

The migration focused on shared connectivity rather than unnecessarily replacing workload infrastructure.

## Real workload testing

The migration did not rely solely on Terraform or Azure control-plane status.

A temporary Production workload generated real traffic through the new network path.

## Packet-level troubleshooting

`tcpdump` helped identify that packets were not reaching Linux on the NVA.

This narrowed the failure to the Azure path and led to discovery of the missing NSG transit rule.

## Governance remained enabled

Azure Policy continued enforcing required tagging even for troubleshooting resources.

The policy was respected instead of bypassed.

## Secretless CI/CD remained intact

OIDC federation continued to be used rather than introducing long-lived Azure credentials.

## Least-privilege cross-subscription access

Private DNS permissions were scoped specifically to the centralized DNS zone.

Broad subscription-level Contributor access was avoided.

## Terraform recovered from partial state

The failed DNS migration did not require manual state reconstruction.

Terraform refreshed actual state and converged forward after the RBAC problem was fixed.

## Cleanup was incremental

Destructive operations were broken into understandable plans.

This made blast radius easier to review.

---

# What Could Be Improved

The migration exposed several opportunities for future platform automation.

## Automatic resource-provider registration

Required Azure resource providers should be registered during subscription bootstrap.

For example:

```text
Microsoft.Network
```

should not first be discovered during application of the networking stack.

## RBAC preflight validation

CI/CD should validate required permissions before Terraform reaches an apply.

The platform could check access to:

- remote state
- subscriptions
- Private DNS
- linked resources
- target resource groups

before attempting infrastructure changes.

## OIDC subject validation

Workflow identity configuration could be automatically tested against:

- branch execution
- pull requests
- GitHub Environments

This would reduce federated-credential troubleshooting.

## Automated data-plane tests

Post-deployment validation should generate actual network traffic automatically.

Examples include:

```text
HTTPS egress test
DNS resolution test
Private Endpoint resolution
Expected public egress IP
Route validation
```

## Better network observability

The platform should consider:

- NSG flow logs
- VNet flow logs
- Azure Network Watcher
- Connection Monitor
- Log Analytics
- NVA metrics
- packet-drop monitoring

## Highly available egress

The current Linux NVA is a single VM.

A production architecture should evaluate:

- multiple NVAs
- Azure Firewall
- active-active architecture
- Availability Zones
- load balancing
- automated failover
- Azure Route Server

---

# Key Engineering Decisions

## Build before destroy

The migration created and validated the replacement environment before deleting the legacy environment.

This reduced migration risk.

## Preserve workload networks

Production and Non-Production networking remained stable while shared connectivity changed around them.

## Separate Terraform ownership

Shared connectivity and workload networking use different Terraform state boundaries.

## Use explicit cross-stack interfaces

The DNS zone ID is exported by the Connectivity stack and consumed by the Network stack.

## Validate the data plane

Actual traffic was required before declaring the migration successful.

## Use least privilege

Cross-subscription permissions were granted at the narrowest practical scope.

## Converge forward after partial failure

Terraform was allowed to reconcile actual infrastructure state rather than attempting unsafe manual rollback.

## Small destructive plans

Legacy infrastructure was dismantled gradually.

---

# Principal-Level Lessons

The migration demonstrated that a platform migration is much more than moving Terraform resources.

The engineering problem crossed several domains:

```text
Architecture
Networking
Terraform
Azure subscriptions
Identity
RBAC
DNS
Security
Governance
CI/CD
Failure recovery
Observability
Migration strategy
```

A Principal engineer needs to reason across these boundaries rather than treat them as isolated technologies.

---

## Lesson 1 — Control Plane Is Not Data Plane

Azure may report:

```text
Succeeded
Connected
Active
```

while user traffic still fails.

Therefore:

> Configuration state is evidence of intended infrastructure. Workload traffic is evidence of actual service health.

---

## Lesson 2 — Follow the Packet

When network behavior is unclear, trace the packet through each boundary.

For this migration:

```text
Workload
   |
   v
Subnet
   |
   v
UDR
   |
   v
Peering
   |
   v
NVA NSG
   |
   v
NVA NIC
   |
   v
Linux forwarding
   |
   v
NAT
   |
   v
Internet
```

This approach avoids random configuration changes.

---

## Lesson 3 — Terraform Apply Is Not a Transaction

Terraform does not automatically roll back every completed operation when a later operation fails.

A failed apply may leave infrastructure partially changed.

The correct recovery model is:

```text
Observe actual state
       |
       v
Identify root cause
       |
       v
Fix dependency
       |
       v
Generate fresh plan
       |
       v
Converge forward
```

---

## Lesson 4 — Saved Plans Are State-Specific

A saved Terraform plan is not a reusable deployment package independent of state.

If state changes:

```text
Old plan
   |
   v
STALE
```

Generate a fresh plan.

---

## Lesson 5 — Authentication Is Not Authorization

OIDC authentication can succeed while the Azure operation still fails.

For example:

```text
GitHub -> Entra authentication
SUCCESS
```

does not mean:

```text
Private DNS join
AUTHORIZED
```

Identity and RBAC must both be correct.

---

## Lesson 6 — Cross-Subscription Architecture Includes RBAC Design

A resource relationship spanning subscriptions also creates an authorization relationship.

For example:

```text
Production Private Endpoint
           |
           v
Connectivity Private DNS Zone
```

requires the identity modifying the Private Endpoint to have rights on the linked DNS zone.

Architecture diagrams should therefore consider:

```text
Resource relationships
+
Identity relationships
+
Permission relationships
```

---

## Lesson 7 — Infrastructure Ownership Matters

The platform originally had connectivity concerns mixed into the Network stack.

The migration clarified ownership:

```text
Connectivity
    |
    +-- shared networking
    +-- hub
    +-- NVA
    +-- peerings
    +-- centralized DNS

Network
    |
    +-- workload VNets
    +-- subnets
    +-- NSGs
    +-- UDRs
    +-- private endpoints
```

Clear ownership reduces Terraform-state coupling.

---

## Lesson 8 — Governance Should Survive Operational Pressure

Temporary troubleshooting infrastructure is still infrastructure.

The tagging policy denied the temporary VM until it complied.

The right response was to satisfy the guardrail rather than disable it.

---

## Lesson 9 — Destructive Changes Should Be Boring

By the time the old environment was destroyed, the risky engineering work had already been completed.

The final cleanup plans were intentionally simple.

That is a desirable migration property.

> The destructive phase should be the least interesting part of the migration.

---

# Interview Story — 60-Second Version

I migrated an Azure hub-and-spoke connectivity platform from a temporary student subscription into a paid shared Connectivity subscription without rebuilding the existing Production and Non-Production spokes.

I built the new hub and Linux NVA, established the new peerings, and changed the spoke default routes to the new NVA. Instead of relying only on Terraform success, I deployed a temporary private Production VM and generated real HTTPS traffic.

The route was correct, but traffic timed out and `tcpdump` on the NVA showed no packets. That told me the failure was before Linux processing. I traced it to the NVA NSG, which allowed SSH but not spoke transit. After adding the transit rule, packet capture showed the full TCP flow through the NVA and Internet egress worked.

I then migrated centralized Private DNS to the paid subscription. That exposed cross-subscription RBAC requirements for both the Terraform Plan and Deploy identities. One apply partially completed before failing, so I corrected the DNS-zone-level RBAC, generated a fresh plan from actual state, and let Terraform converge forward.

After validating the new Key Vault DNS records and traffic path, I removed the old peerings, hub resources, DNS zone, and finally the old resource group in controlled cleanup stages.

---

# Interview Story — STAR Version

## Situation

Shared Azure connectivity was hosted in a temporary student subscription while Production and Non-Production already existed in separate subscriptions.

The platform needed to move shared connectivity into a paid Connectivity subscription without rebuilding the spokes or creating unnecessary downtime.

## Task

Design and execute a safe migration of:

- hub networking
- centralized egress
- NVA
- hub/spoke connectivity
- Private DNS

while preserving the existing spoke networks and maintaining CI/CD, governance, and Terraform-state integrity.

## Action

I used a staged migration strategy.

First, I built the new paid hub and NVA using Terraform.

I established new peerings while keeping the old connectivity path available.

I changed Production and Non-Production default routes to point to the new NVA.

I then created a temporary private Production VM and generated real HTTPS traffic.

Although the effective route was correct, the connection timed out.

I used `tcpdump` on the NVA and saw no packets, which narrowed the failure to the Azure path before Linux.

I identified a missing NSG rule allowing spoke transit traffic into the NVA.

After deploying the rule, the packet capture showed successful bidirectional TCP traffic through the NVA.

Next, I migrated the centralized Key Vault Private DNS zone into the paid Connectivity subscription.

The Connectivity stack exported the DNS zone ID through remote state, and the Network stack consumed it.

During the cutover, cross-subscription DNS operations exposed missing RBAC for the Terraform deployment identity.

The apply partially completed before failing.

Rather than manually restoring resources, I corrected the least-privilege DNS permissions, generated a fresh plan, and allowed Terraform to reconcile forward.

I also corrected equivalent read permissions for the Terraform Plan identity.

After validating the new Production and Non-Production Key Vault DNS records, I removed the old peerings and legacy hub infrastructure incrementally.

The final cleanup removed only the now-empty old resource group.

## Result

The migration completed successfully.

Production and Non-Production retained their original VNets and addressing.

Their Internet traffic now uses the new paid Connectivity NVA.

Private DNS is centrally owned by the paid Connectivity subscription.

The temporary student connectivity environment was completely retired.

The migration also produced a cleaner Terraform ownership model and identified opportunities for automated post-deployment network validation and RBAC preflight testing.

---

# Questions I Should Be Able to Answer in an Interview

After completing this migration, I should be able to explain:

1. Why build-before-destroy is safer than replacing the hub directly.
2. Why a successful Terraform apply does not prove network health.
3. How UDR traffic reaches a Virtual Appliance.
4. Why Azure NSGs can prevent packets from ever reaching Linux.
5. What `tcpdump` proved during the investigation.
6. Why ping and Internet egress testing prove different things.
7. Why an NVA needs IP forwarding enabled.
8. Why NAT is required for centralized Internet egress.
9. Why Terraform saved plans become stale.
10. Why Terraform apply is not transactional.
11. How to recover safely from a partial Terraform apply.
12. Why state locking should not be disabled to solve RBAC failures.
13. How GitHub Actions OIDC authentication works.
14. Why OIDC subject claims differ between branches and environments.
15. Why successful authentication does not imply authorization.
16. Why Private Endpoint-to-DNS-zone relationships require linked-resource RBAC.
17. Why the Terraform Plan identity needed DNS read permissions.
18. Why the Deploy identity needed DNS join permissions.
19. Why centralized Private DNS belongs with shared connectivity.
20. Why explicit Terraform ownership boundaries matter.
21. Why remote-state outputs are better than duplicating resource ownership.
22. Why IP-address changes can be blocked by active NIC allocations.
23. Why destructive migration plans should be kept small.
24. What I would change to make the NVA highly available.
25. When I would choose Azure Firewall instead of a Linux NVA.

---

# Follow-Up Engineering Work

The migration is complete, but the platform can be improved further.

Priority follow-up work includes:

```text
Automated network smoke tests
Automated DNS-resolution tests
Cross-subscription RBAC preflight checks
OIDC federation validation
Resource-provider bootstrap
NSG / VNet flow logging
NVA observability
Connectivity SLOs
Highly available egress
Azure Firewall evaluation
Azure Route Server evaluation
Failure and rollback runbooks
```

---

# Result

The connectivity migration is complete.

The paid Connectivity subscription is now the authoritative owner of:

```text
Shared hub networking
Centralized Internet egress
NVA infrastructure
Hub/spoke peerings
Centralized Private DNS
```

Production and Non-Production remain responsible for their workload-facing networking while consuming the centralized services.

The temporary student connectivity environment has been fully retired.

The migration established a cleaner platform architecture and demonstrated an operational approach based on:

```text
Build safely
Validate deeply
Diagnose by boundaries
Recover forward
Destroy last
```

---

# Final Principle

> Build the replacement first. Validate it from the workload's point of view. Preserve the rollback path until the new data plane is proven. Then remove the old system in small, controlled steps.