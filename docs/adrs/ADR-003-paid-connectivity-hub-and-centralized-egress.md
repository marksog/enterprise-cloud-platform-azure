# ADR-003: Paid Connectivity Hub and Centralized Egress

- **Status:** Accepted
- **Date:** 2026-09-12
- **Decision Owners:** Platform Engineering / Networking
- **Scope:** Azure landing-zone connectivity, centralized egress, Private DNS, Terraform ownership, and CI/CD identity boundaries

---

## 1. Context

The Azure enterprise platform uses a hub-and-spoke networking architecture with separate subscriptions for shared platform services, Production, and Non-Production workloads.

The original connectivity hub was deployed in a student subscription and used the address space:

```text
10.0.0.0/20
```

The workload spokes use:

```text
Production:      10.10.0.0/20
Non-Production:  10.20.0.0/20
```

The original hub hosted shared connectivity resources including:

- Hub virtual network
- Hub subnets
- Network Virtual Appliance networking
- Centralized Private DNS
- Hub-to-spoke connectivity
- Shared routing infrastructure

As the platform evolved, the student subscription became unsuitable for hosting long-lived shared connectivity infrastructure.

The platform therefore required migration of shared connectivity services into the paid Connectivity subscription.

The migration had several important constraints:

1. Production and Non-Production VNets should not be recreated.
2. Existing spoke address spaces should remain unchanged.
3. The migration should minimize disruption.
4. Traffic should not move until the replacement path was ready.
5. The old infrastructure should remain available until the new path was validated.
6. Infrastructure ownership between Terraform stacks should become clearer.
7. GitHub Actions should continue using secretless OIDC authentication.
8. Cross-subscription access should follow least-privilege principles.

---

## 2. Decision

Shared Azure connectivity services will be hosted in the paid Connectivity subscription.

The platform will maintain a clear ownership boundary between the **Connectivity** and **Network** Terraform stacks.

### Connectivity Terraform stack

```text
terraform/connectivity/
```

The Connectivity stack owns shared connectivity infrastructure including:

- Paid hub VNet
- Hub subnets
- Network Virtual Appliance
- NVA network interface
- NVA public IP
- NVA Network Security Group
- Hub-to-spoke peerings
- Spoke-to-hub peerings
- Centralized Private DNS zones
- Connectivity-specific Terraform state

### Network Terraform stack

```text
terraform/network/
```

The Network stack owns workload-facing networking including:

- Production spoke VNet
- Non-Production spoke VNet
- Production subnets
- Non-Production subnets
- Network Security Groups
- Route tables
- Route-table associations
- Key Vaults
- Private Endpoints
- VNet links consuming centralized Private DNS

This boundary prevents multiple Terraform states from owning the same Azure infrastructure.

---

## 3. Target Network Architecture

The new paid connectivity hub uses:

```text
10.30.0.0/20
```

The Production spoke remains:

```text
10.10.0.0/20
```

The Non-Production spoke remains:

```text
10.20.0.0/20
```

The Network Virtual Appliance uses:

```text
10.30.0.196
```

The resulting high-level topology is:

```text
                         Internet
                            |
                            |
                            v
                    +----------------+
                    |      NVA       |
                    |  10.30.0.196   |
                    +----------------+
                            |
                            |
                 +----------+----------+
                 |                     |
                 |                     |
                 v                     v

       +------------------+     +------------------+
       | Production Spoke |     | NonProd Spoke    |
       |  10.10.0.0/20    |     |  10.20.0.0/20   |
       +------------------+     +------------------+

                 \                     /
                  \                   /
                   \                 /
                    +---------------+
                    | Paid Hub VNet |
                    | 10.30.0.0/20  |
                    +---------------+
```

The original `10.0.0.0/20` student-subscription hub is retired after successful migration and validation.

---

## 4. Centralized Egress

Production and Non-Production workloads use User Defined Routes to direct Internet-bound traffic through the centralized NVA.

The default route is:

```text
0.0.0.0/0
    |
    v
Virtual Appliance
10.30.0.196
```

For example, Production application traffic follows:

```text
Production workload
10.10.x.x
     |
     v
Production UDR
0.0.0.0/0
     |
     v
Virtual Appliance
10.30.0.196
     |
     v
Paid Hub
     |
     v
NVA
     |
     v
IP forwarding
     |
     v
NAT / MASQUERADE
     |
     v
Internet
```

Non-Production uses the equivalent architecture from the `10.20.0.0/20` spoke.

---

## 5. NVA Design

The lab uses a Linux Network Virtual Appliance.

The NVA provides:

- IP forwarding
- Centralized routing
- Transit filtering
- NAT
- Internet egress

Linux IP forwarding is enabled.

The NVA uses `iptables` to implement forwarding and NAT behavior.

Internet-bound workload traffic is source NATed using MASQUERADE.

Conceptually:

```text
Spoke workload
      |
      v
Azure UDR
      |
      v
NVA NIC
      |
      v
Linux FORWARD chain
      |
      v
iptables policy
      |
      v
POSTROUTING MASQUERADE
      |
      v
Internet
```

This NVA is intentionally a cost-conscious lab implementation.

It is not considered equivalent to a fully managed enterprise firewall.

For production enterprise use, managed services such as Azure Firewall or a supported enterprise NVA should be evaluated.

---

## 6. Layered Transit Security

The architecture uses multiple enforcement layers.

### Layer 1 — Azure NSG

The NVA NSG permits transit traffic from the spoke address spaces:

```text
10.10.0.0/20
10.20.0.0/20
```

The purpose of this rule is to allow legitimate spoke traffic to reach the NVA.

### Layer 2 — Linux forwarding policy

The Linux NVA performs more granular forwarding decisions.

Application and AKS networks may be permitted to transit.

Data networks may be denied general Internet transit.

The model is therefore:

```text
Spoke
  |
  v
Azure NSG
  |
  v
NVA operating system
  |
  v
iptables FORWARD policy
  |
  v
NAT
  |
  v
Internet
```

The NSG answers:

> Is this traffic allowed to reach the NVA?

The Linux forwarding policy answers:

> Is this workload network allowed to transit through the NVA?

This provides layered controls instead of relying on a single enforcement point.

---

## 7. Centralized Private DNS

Centralized Azure Private DNS is hosted in the paid Connectivity subscription.

The Key Vault Private DNS zone is:

```text
privatelink.vaultcore.azure.net
```

The paid hub, Production, and Non-Production networks consume the centralized DNS service through VNet links.

The resulting model is:

```text
Paid Connectivity Subscription
|
+-- privatelink.vaultcore.azure.net
      |
      +-- Paid Hub VNet link
      |
      +-- Production VNet link
      |
      +-- Non-Production VNet link
```

Production and Non-Production Key Vault Private Endpoints use DNS zone groups associated with this centralized zone.

This ensures that workloads resolve Key Vault names to private endpoint addresses rather than public endpoints.

---

## 8. Cross-Stack Terraform Dependency

The Connectivity Terraform stack owns the Private DNS zone.

The Network Terraform stack needs the zone ID when creating:

- Production DNS VNet links
- Non-Production DNS VNet links
- Production Key Vault Private Endpoint DNS zone groups
- Non-Production Key Vault Private Endpoint DNS zone groups

The Connectivity stack therefore exports:

```hcl
output "key_vault_private_dns_zone_id" {
  description = "Resource ID of the centralized Key Vault Private DNS zone."
  value       = azurerm_private_dns_zone.key_vault.id
}
```

The Network stack consumes the output through Terraform remote state.

Conceptually:

```text
terraform/connectivity
        |
        |
        | key_vault_private_dns_zone_id
        |
        v
connectivity.tfstate
        |
        v
terraform/network
```

This avoids hardcoding the complete Azure resource ID and provides an explicit interface between Terraform stacks.

---

## 9. Terraform State Ownership

The platform deliberately separates Terraform state according to infrastructure responsibility.

### Connectivity state

Owns shared connectivity infrastructure.

```text
terraform/connectivity/
```

### Network state

Owns spoke and workload-facing network infrastructure.

```text
terraform/network/
```

A resource must have one authoritative Terraform owner.

Resources must not be simultaneously managed by both states.

Cross-stack relationships should be implemented through explicit outputs, remote state, or another controlled interface.

---

## 10. CI/CD Authentication

GitHub Actions authenticates to Azure using OpenID Connect federation.

The architecture avoids storing long-lived Azure client secrets in GitHub.

Separate identities are used for planning and deployment.

Conceptually:

```text
GitHub Actions
      |
      v
GitHub OIDC token
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

The federated identity subject must match the GitHub execution context.

Different execution contexts may produce subjects corresponding to:

- Pull requests
- Main branch
- GitHub environments

Federated credentials must therefore be configured for the execution contexts used by the workflows.

---

## 11. Plan and Deploy Identity Separation

Terraform Plan and Terraform Apply use separate identities.

This provides a clearer privilege boundary.

### Plan identity

The Plan identity requires enough access to:

- Read Terraform state
- Refresh Azure resources
- Read cross-subscription dependencies
- Acquire Terraform state locks
- Generate an accurate execution plan

### Deploy identity

The Deploy identity requires permissions to:

- Perform approved infrastructure changes
- Update network resources
- Join linked resources
- Manage required DNS relationships

This separation reduces unnecessary write permissions during pull-request validation.

---

## 12. Cross-Subscription RBAC

The architecture requires controlled cross-subscription operations.

For example, the Network Terraform stack manages resources in Production and Non-Production while consuming a Private DNS zone owned by the Connectivity subscription.

Azure therefore requires permissions on both sides of certain linked-resource operations.

The Network identities require appropriate permissions on:

```text
privatelink.vaultcore.azure.net
```

in the paid Connectivity subscription.

The permission is granted at the narrowest practical scope.

Rather than assigning broad Contributor access across the Connectivity subscription, DNS permissions are scoped to the specific Private DNS zone.

This follows the principle of least privilege.

---

## 13. Migration Strategy

The migration used a staged approach rather than a destructive replacement.

The strategy was:

```text
Build replacement infrastructure
            |
            v
Establish connectivity
            |
            v
Validate control plane
            |
            v
Cut spoke routes to new NVA
            |
            v
Validate actual data plane
            |
            v
Migrate centralized DNS
            |
            v
Validate DNS
            |
            v
Remove old peerings
            |
            v
Remove old hub resources
            |
            v
Remove old resource group
```

The old environment was retained until the new environment had been validated.

This reduced blast radius and preserved a rollback path during the migration.

---

## 14. Why the Old Hub Was Not Destroyed First

Destroying the original hub before validating the replacement would have created unnecessary risk.

If the new architecture failed after the old path had already been destroyed, restoring connectivity would require rebuilding infrastructure during an outage.

Instead, the platform followed:

```text
Old path available
        +
New path built
        |
        v
New path validated
        |
        v
Traffic cut over
        |
        v
Old path retired
```

This is safer than:

```text
Destroy old
    |
    v
Build new
    |
    v
Hope it works
```

---

## 15. Data-Plane Validation

A successful Terraform apply does not prove that workload traffic can actually traverse the network.

The migration therefore included explicit data-plane validation.

A temporary Production VM was deployed into the Production application subnet.

The VM had no public IP.

Its effective route was inspected and confirmed:

```text
0.0.0.0/0
    |
    v
VirtualAppliance
    |
    v
10.30.0.196
```

The VM then generated HTTPS traffic toward the Internet.

The NVA captured traffic using:

```bash
sudo tcpdump -ni any host 10.10.0.4
```

The capture demonstrated traffic originating from the Production workload and traversing the NVA.

TCP traffic included the expected connection sequence:

```text
Production VM
     |
     | SYN
     v
Internet endpoint
     |
     | SYN-ACK
     v
Production VM
```

Application traffic and return traffic were observed.

This proved:

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
NAT
       |
       v
Internet
       |
       v
Return path
       |
       v
Production workload
```

This was considered stronger evidence than simply observing Azure resources in a `Succeeded` state.

---

## 16. Missing NVA Transit Rule Discovered During Validation

Initial control-plane checks appeared healthy.

The Production VM showed an active route:

```text
0.0.0.0/0
→ VirtualAppliance
→ 10.30.0.196
```

However, HTTPS traffic from the VM timed out.

Packet capture on the NVA showed no packets from the Production VM.

This indicated that the failure occurred before traffic reached the Linux operating system.

Investigation identified the NVA NSG as the missing enforcement layer.

The NSG originally allowed administrative SSH access but did not explicitly permit spoke transit traffic to reach the NVA.

A spoke-transit NSG rule was added.

After deployment, packet capture immediately showed Production traffic traversing the NVA.

The lesson was:

> Correct routes and healthy peerings do not prove that the data plane is operational.

Network validation must include actual workload-generated traffic.

---

## 17. Private DNS Migration

The original Private DNS zone was hosted in the student connectivity subscription.

The migration could not simply delete the old DNS zone and recreate everything immediately because Production and Non-Production Private Endpoints depended on it.

The DNS migration therefore used another staged cutover.

### Stage 1

Create the new DNS zone in the paid Connectivity subscription.

### Stage 2

Expose the new zone ID through Connectivity Terraform state.

### Stage 3

Allow the Network stack to consume the new zone ID.

### Stage 4

Move Production and Non-Production VNet links to the new zone.

### Stage 5

Move Private Endpoint DNS zone groups to the new zone.

### Stage 6

Validate that the new DNS zone contains records for:

```text
sog-prod-kv
sog-nonprod-kv
```

### Stage 7

Delete the old DNS zone.

This avoided destroying the authoritative DNS dependency before the replacement was operational.

---

## 18. Partial Apply Recovery

During the DNS migration, Terraform successfully destroyed some old DNS links before encountering an authorization failure against the new cross-subscription DNS zone.

The deployment failed because the Network deployment identity could modify the Private Endpoint resources but did not have permission to perform required actions against the new Private DNS zone.

The failed operation demonstrated an important Terraform property:

> An apply is not a database transaction.

Some resources may already have changed before a later operation fails.

The recovery approach was:

1. Do not manually attempt to reconstruct the previous state.
2. Identify the authorization failure.
3. Grant the minimum required RBAC.
4. Generate a fresh Terraform plan.
5. Allow Terraform to refresh actual Azure state.
6. Reconcile the partially completed deployment.
7. Apply the new plan.

Terraform converged the environment successfully after the RBAC issue was corrected.

---

## 19. Terraform Saved Plan Staleness

During the migration, an earlier saved Terraform plan became stale after another operation changed Terraform state.

Terraform correctly rejected the plan with:

```text
Saved plan is stale
```

The plan was not forced or reused.

Instead, a new plan was generated from the current state.

This reinforced the rule:

> A saved Terraform plan is valid only for the exact state snapshot against which it was created.

When state changes, regenerate the plan.

---

## 20. Terraform State Locking

Terraform state locking was used to protect remote state against concurrent writes.

An early workflow encountered a state-lock authorization failure because the CI/CD identity lacked the required storage permissions.

The solution was to correct Azure RBAC rather than bypass locking.

The platform does not use:

```text
-lock=false
```

as a normal workaround.

Disabling locking would remove an important protection against concurrent state modification.

---

## 21. Azure Resource Provider Registration

During deployment of the new connectivity environment, Azure initially rejected Virtual Network creation because the subscription had not registered:

```text
Microsoft.Network
```

The resource provider was registered before retrying deployment.

The lesson is that subscription bootstrap must include required Azure resource-provider registration.

Future platform bootstrap automation should explicitly account for required providers rather than discovering them only during workload deployment.

---

## 22. Subnet Address Migration Constraint

During hub readdressing, Azure rejected an attempted subnet change because the requested subnet range was outside the VNet's current address space.

Another attempted subnet change was blocked because the old subnet prefix still contained active allocations.

This demonstrated that network address changes cannot always be performed as simple in-place Terraform modifications.

Resources such as NICs create allocation dependencies.

The migration therefore required careful sequencing:

```text
Create valid address space
       |
       v
Create replacement subnet
       |
       v
Move/recreate dependent allocation
       |
       v
Remove old subnet
```

The general lesson is:

> IP address architecture should be treated as a structural design decision, not a cosmetic Terraform variable.

---

## 23. OIDC Federated Identity Troubleshooting

GitHub Actions initially failed Azure authentication because Microsoft Entra ID could not find a federated identity matching the OIDC subject presented by GitHub.

Different workflow contexts generated subjects such as:

```text
repo:<repository>:pull_request
```

and:

```text
repo

## 23. OIDC Federated Identity Troubleshooting

GitHub Actions initially failed Azure authentication because Microsoft Entra ID could not find a federated identity credential matching the OIDC subject presented by GitHub.

Different workflow execution contexts produced different subject claims.

Examples included:

```text
repo:<repository>:pull_request
```

for pull-request workflows,

```text
repo:<repository>:ref:refs/heads/main
```

for workflows running directly from the `main` branch, and:

```text
repo:<repository>:environment:<environment-name>
```

for jobs associated with a GitHub Environment.

The important lesson was that OIDC federation is not simply:

```text
GitHub repository
        |
        v
Azure
```

The actual trust relationship is:

```text
GitHub execution context
        |
        v
OIDC subject claim
        |
        v
Microsoft Entra federated credential
        |
        v
Azure identity
```

The federated credential must match:

- issuer
- subject
- audience

The GitHub OIDC issuer is:

```text
https://token.actions.githubusercontent.com
```

The Azure workload identity federation audience is:

```text
api://AzureADTokenExchange
```

Federated credentials were created for the GitHub execution contexts required by the platform workflows.

This allowed authentication without storing long-lived client secrets in GitHub.

---

## 24. State Lock Authorization Failure

Terraform remote state was stored in Azure Storage.

During early CI/CD execution, Terraform was able to authenticate to Azure but failed while acquiring the state lock.

The error indicated:

```text
AuthorizationPermissionMismatch
```

This demonstrated an important distinction:

> Successful Azure authentication does not imply authorization to every dependent platform service.

Terraform required sufficient storage data-plane permissions to:

- read state
- write state
- create/update lock metadata
- release the lock

The correct response was to grant the required RBAC permissions.

The lock was not disabled.

This preserved Terraform's concurrency protection.

---

## 25. Azure Resource Provider Registration Failure

The first attempt to deploy the new hub VNet failed with:

```text
MissingSubscriptionRegistration
```

for:

```text
Microsoft.Network
```

The paid subscription had not yet registered the Network resource provider.

The provider was registered before retrying.

This highlighted a platform-bootstrap dependency:

```text
Subscription
     |
     v
Required providers registered
     |
     v
Platform infrastructure
```

A mature landing-zone bootstrap process should register required providers before downstream Terraform stacks attempt resource creation.

---

## 26. Stale Saved Plan Recovery

A previously generated Terraform plan later failed with:

```text
Saved plan is stale
```

The reason was that Terraform state had changed after the plan was generated.

Terraform saved plans are tied to the state snapshot against which they were created.

The correct recovery was:

```text
state changed
     |
     v
discard old plan
     |
     v
terraform plan again
     |
     v
review new plan
     |
     v
apply
```

The old plan was not forced.

This preserved the integrity of the plan-review-apply workflow.

---

## 27. Hub Address-Space Migration

The original hub used:

```text
10.0.0.0/20
```

The replacement paid hub uses:

```text
10.30.0.0/20
```

An early migration attempt tried to introduce a subnet whose address prefix did not belong to the current VNet address space.

Azure correctly rejected the operation.

Another attempted subnet-prefix change failed because an existing NIC had an active private IP allocation in the subnet.

The error demonstrated that the following are not independent Terraform values:

```text
VNet CIDR
   |
   v
Subnet CIDR
   |
   v
NIC allocation
   |
   v
Workload
```

Changing an upstream addressing decision can require recreation or migration of downstream allocations.

The eventual migration strategy used a replacement network path rather than forcing an unsafe in-place change.

---

## 28. Active Allocation Preventing Subnet Mutation

Azure rejected removal of an old subnet prefix with:

```text
InUsePrefixCannotBeDeleted
```

because the old NVA NIC still had an active allocation in the subnet.

The correct dependency order was:

```text
Dependent VM
     |
     v
NIC
     |
     v
Subnet
     |
     v
VNet
```

Resources must be moved or destroyed from the bottom of the dependency chain before upstream network ranges can be removed.

This reinforced the importance of understanding cloud-resource dependency graphs rather than treating Terraform as a text-replacement engine.

---

## 29. Runtime Validation Exposed a Control-Plane/Data-Plane Gap

One of the most important findings during the migration was that Azure control-plane configuration looked healthy before the system was actually usable.

The following were all correct:

```text
VNet peerings       healthy
Route tables        configured
Effective route     correct
NVA running         yes
Terraform apply     successful
```

Yet Production workload traffic still could not reach the Internet.

The missing NSG transit permission prevented packets from reaching Linux.

This distinction is critical:

```text
Control plane
     !=
Data plane
```

A Principal-level network validation process must verify both.

---

## 30. Why `tcpdump` Was Used

The migration used packet capture on the NVA to determine where traffic disappeared.

The command:

```bash
sudo tcpdump -ni any host 10.10.0.4
```

did not generate traffic.

It passively observed traffic where the Production test VM was either the source or destination.

The test was structured as:

```text
Terminal 1
NVA:
tcpdump listening

Terminal 2
Production VM:
HTTPS request to Internet
```

Initially:

```text
Production VM sends traffic
        |
        v
No packet appears on NVA
```

This localized the failure to the path before Linux processing.

After the NSG fix:

```text
Production VM sends traffic
        |
        v
tcpdump sees packets
        |
        v
NVA forwards
        |
        v
Internet response returns
```

Packet capture provided direct evidence of data-plane behavior.

---

## 31. Temporary Workload Validation

The Production and Non-Production spokes did not initially contain workloads that could generate realistic traffic.

A temporary Production VM was therefore created specifically for validation.

The VM:

- had no public IP
- was placed inside the Production application subnet
- inherited the Production route table
- used the NVA for default Internet egress

Azure Run Command was used to execute connectivity tests without exposing SSH directly to the temporary workload.

After validation, the temporary VM and NIC were deleted.

This kept the permanent platform clean while still enabling realistic testing.

---

## 32. Governance Guardrail Validation

The first temporary VM deployment failed because enterprise policy required a `CostCenter` tag.

The platform did not bypass or disable the governance policy.

Instead, the temporary test infrastructure was changed to comply with the required tagging contract.

The result demonstrated that governance remained active even during troubleshooting.

The principle followed was:

> Troubleshooting resources should comply with platform guardrails rather than receive exceptions by default.

This is important because operational pressure is often when teams are most tempted to bypass controls.

---

## 33. Cross-Subscription DNS Authorization Failure

During Private DNS migration, the Network deployment identity could modify resources in Production and Non-Production but did not initially have permission on the new Connectivity-owned DNS zone.

Azure returned a linked authorization failure for:

```text
Microsoft.Network/privateDnsZones/join/action
```

The deployment identity therefore required permission on both sides of the relationship:

```text
Private Endpoint
       |
       | managed by Network identity
       |
       v
Private DNS zone
       |
       | owned by Connectivity subscription
       |
       v
Cross-subscription authorization required
```

The identity received `Private DNS Zone Contributor` scoped to the specific centralized DNS zone.

Broad subscription-level Contributor access was not required.

---

## 34. Plan Identity Also Required Cross-Subscription Read Access

After the deployment identity was fixed, a later Terraform plan failed while refreshing the newly created DNS VNet links.

The Plan identity did not have permission to read:

```text
Microsoft.Network/privateDnsZones/virtualNetworkLinks/read
```

in the Connectivity subscription.

This highlighted another important principle:

> Read-only planning still requires visibility into every resource represented in Terraform state.

The Plan identity was granted the required DNS-zone-level role.

After that, Terraform could refresh state and generate an accurate plan.

---

## 35. Cleanup Strategy

Legacy resources were removed incrementally rather than using a single large destructive operation.

Cleanup proceeded approximately as follows:

```text
1. Cut routes to new NVA
2. Validate real traffic
3. Remove old hub peerings
4. Migrate centralized DNS
5. Validate new DNS records
6. Remove old DNS zone
7. Remove old NVA NIC/public IP
8. Remove old hub subnets
9. Remove old hub VNet
10. Remove old resource group
```

This sequencing reduced risk and made every destructive plan easier to review.

For example, one cleanup plan intentionally contained only:

```text
0 to add
0 to change
4 to destroy
```

for old peerings.

A later plan contained only legacy hub infrastructure.

The final plan contained:

```text
0 to add
0 to change
1 to destroy
```

where the single resource was the now-empty old connectivity resource group.

This made destructive changes understandable and auditable.

---

## 36. Rollback Philosophy

The migration favored reversible changes until validation was complete.

Before route cutover:

```text
Old hub available
New hub available
```

If validation had failed, spoke routes could remain pointed at the old NVA.

Once traffic was successfully validated through the new path, rollback risk decreased.

DNS followed the same philosophy.

The old DNS zone remained available until:

- the new zone existed
- VNet links were migrated
- Private Endpoint DNS zone groups were updated
- new records were verified

Only after successful validation was the old zone removed.

---

## 37. Operational Lessons

The migration produced several operational lessons.

### 37.1 Authentication and authorization are different

OIDC authentication can succeed while Azure RBAC still prevents the required operation.

### 37.2 Terraform plans are snapshots

A saved plan cannot safely survive unrelated state changes.

### 37.3 Terraform applies are not transactions

Partial changes may remain after an apply failure.

### 37.4 State locking must remain enabled

Lock failures should be fixed through RBAC rather than bypassed.

### 37.5 Network configuration is not network validation

Routes and peerings can look correct while packets are still being dropped.

### 37.6 Packet capture is a powerful isolation tool

Observing traffic at the expected transit point helps identify where the path breaks.

### 37.7 Cross-subscription design introduces identity dependencies

Resource ownership and deployment identity permissions must be designed together.

### 37.8 Destructive migration steps should be small

Small cleanup plans make blast radius and review much easier to understand.

### 37.9 Shared services need explicit ownership

DNS, routing, NVA resources, and peerings should have clear Terraform owners.

### 37.10 Governance should remain active during troubleshooting

Temporary resources should comply with platform policies.

---

## 38. Security Considerations

The architecture deliberately applies multiple security controls.

### Secretless CI/CD

GitHub Actions uses OIDC federation rather than stored Azure client secrets.

### Least privilege

Cross-subscription access is scoped to required resources wherever practical.

### Network segmentation

Production and Non-Production remain in separate subscriptions and VNets.

### Centralized egress

Spoke Internet traffic traverses a controlled network path.

### Layered transit enforcement

Azure NSGs and Linux forwarding controls both participate in the traffic decision.

### Private service access

Key Vault uses Private Endpoints with centralized Private DNS.

### Governance enforcement

Azure Policy requirements remain active for resources including temporary validation infrastructure.

---

## 39. Availability Considerations

The current lab NVA is a single virtual machine.

This creates a known single point of failure for centralized Internet egress.

This is acceptable for the current learning environment but would not meet a production high-availability standard.

A future enterprise design should evaluate:

- multiple NVA instances
- load-balanced NVAs
- Azure Firewall
- availability-zone placement
- health probes
- automated failover
- Azure Route Server
- active-active routing architectures

The current implementation is intended to teach routing, forwarding, NAT, Terraform, and operational troubleshooting rather than represent the final production HA topology.

---

## 40. Observability Considerations

Future versions of the platform should provide stronger network telemetry.

Candidate improvements include:

- NSG flow logs
- Azure Network Watcher
- Connection Monitor
- VNet flow logs
- centralized Log Analytics
- NVA system logs
- iptables metrics
- packet-drop monitoring
- route-change alerting
- DNS-resolution monitoring
- synthetic egress tests

The migration demonstrated that connectivity failures can occur even when infrastructure deployment succeeds.

Automated telemetry should therefore focus on service behavior rather than infrastructure state alone.

---

## 41. Automated Post-Deployment Validation

A future platform improvement should add automated smoke testing after connectivity changes.

Tests could include:

```text
Prod test endpoint
      |
      +-- DNS resolution
      +-- Internet HTTPS access
      +-- expected public egress IP
      +-- Key Vault private resolution
      +-- route validation

NonProd test endpoint
      |
      +-- DNS resolution
      +-- Internet HTTPS access
      +-- expected public egress IP
      +-- Key Vault private resolution
      +-- route validation
```

Successful infrastructure deployment should be followed by service-level validation.

The desired pipeline becomes:

```text
terraform plan
      |
      v
approval
      |
      v
terraform apply
      |
      v
network smoke tests
      |
      v
deployment declared healthy
```

---

## 42. Cost Considerations

The current Linux NVA was chosen partly to control lab cost.

This provides useful hands-on experience with:

- Linux forwarding
- NAT
- packet capture
- route tables
- NSGs
- troubleshooting

The tradeoff is increased operational responsibility.

Managed firewall services may cost more but reduce responsibility for:

- operating-system maintenance
- HA implementation
- patching
- forwarding configuration
- firewall-engine lifecycle

Cost decisions should therefore account for engineering and operational effort, not only Azure resource price.

---

## 43. Alternatives Considered

### 43.1 Continue using the student-subscription hub

Rejected.

The student subscription was not considered an appropriate long-term home for shared platform services.

### 43.2 Destroy the old hub and rebuild from scratch

Rejected.

This would unnecessarily increase outage and recovery risk.

### 43.3 Recreate Production and Non-Production spokes

Rejected.

The workload networks did not require replacement.

### 43.4 Allow direct Internet access from each spoke

Rejected.

Centralized egress provides a common enforcement and observability point.

### 43.5 Deploy Azure Firewall immediately

Deferred.

The Linux NVA provides a lower-cost environment for learning and validating routing fundamentals.

Azure Firewall remains a candidate for a future production-grade architecture.

### 43.6 Keep DNS in the old subscription

Rejected.

Shared DNS belongs with shared connectivity infrastructure and should not keep the platform dependent on the retired subscription.

---

## 44. Consequences

### Positive consequences

The new design provides:

- clearer Terraform ownership
- centralized connectivity
- centralized Private DNS
- centralized egress
- secretless CI/CD authentication
- least-privilege cross-subscription authorization
- cleaner separation between shared and workload infrastructure
- staged migration capability
- stronger operational knowledge of the data path

### Negative consequences

The architecture introduces:

- remote-state dependencies
- cross-subscription RBAC complexity
- reliance on centralized connectivity
- NVA operational responsibility
- a single-NVA availability limitation in the current lab
- additional CI/CD identity configuration

These tradeoffs are accepted for the current platform stage.

---

## 45. Final Architecture

After migration and cleanup:

```text
Azure Platform
|
+-- Connectivity Subscription
|     |
|     +-- Paid Hub VNet
|     |     10.30.0.0/20
|     |
|     +-- NVA
|     |     10.30.0.196
|     |
|     +-- NVA NSG
|     |
|     +-- Hub/Spoke Peerings
|     |
|     +-- Central Private DNS
|           privatelink.vaultcore.azure.net
|
+-- Production Subscription
|     |
|     +-- Production VNet
|     |     10.10.0.0/20
|     |
|     +-- Application subnet
|     +-- Data subnet
|     +-- Private Endpoint subnet
|     +-- AKS subnet
|     |
|     +-- Route table
|     |     0.0.0.0/0 -> 10.30.0.196
|     |
|     +-- Key Vault Private Endpoint
|
+-- Non-Production Subscription
      |
      +-- NonProd VNet
      |     10.20.0.0/20
      |
      +-- Application subnet
      +-- Data subnet
      +-- Private Endpoint subnet
      +-- AKS subnet
      |
      +-- Route table
      |     0.0.0.0/0 -> 10.30.0.196
      |
      +-- Key Vault Private Endpoint
```

The old student connectivity environment has been retired.

---

## 46. Principal Engineering Takeaways

The most important engineering outcome was not simply moving resources between subscriptions.

The migration required reasoning about:

- resource ownership
- failure domains
- Terraform state
- Azure dependency graphs
- network control plane
- network data plane
- OIDC identity
- RBAC
- cross-subscription relationships
- DNS dependencies
- staged rollout
- rollback
- production validation
- cleanup sequencing

The key architectural principle is:

> Build the replacement, prove it works from the workload's point of view, and only then remove the old path.

The key operational principle is:

> Infrastructure state is evidence of configuration; workload behavior is evidence of service health.

The key Terraform principle is:

> Terraform should continuously reconcile actual infrastructure toward declared intent, including after partial failures.

The key security principle is:

> Cross-subscription capability should be granted intentionally and at the narrowest practical scope.

---

## 47. Decision Outcome

The migration is complete.

The paid Connectivity subscription is now the authoritative owner of shared Azure connectivity services.

Production and Non-Production continue to own their workload networks while consuming centralized:

- routing
- Internet egress
- hub connectivity
- Private DNS

The original student-subscription connectivity infrastructure has been retired.

This architecture is accepted as the current Azure platform networking baseline.

---

## 48. Future Work

Future iterations should evaluate:

- highly available NVA architecture
- Azure Firewall
- Azure Route Server
- zone-resilient connectivity
- automated network smoke tests
- automated Private DNS tests
- flow logging
- Network Watcher integration
- centralized observability
- route-change monitoring
- configuration drift detection
- automated resource-provider registration
- policy-as-code validation for networking
- automated RBAC validation
- disaster recovery procedures
- formal connectivity SLOs

---

## 49. Review Triggers

This ADR should be reviewed if any of the following occur:

- migration from the Linux NVA to Azure Firewall
- introduction of additional workload spokes
- multi-region expansion
- introduction of ExpressRoute
- site-to-site VPN implementation
- adoption of Azure Route Server
- significant Private DNS architecture changes
- change to Terraform state boundaries
- replacement of GitHub Actions identity architecture
- implementation of highly available centralized egress

---

## 50. Status

**Accepted**

The architecture described in this ADR represents the current target state for Azure shared connectivity and centralized egress.