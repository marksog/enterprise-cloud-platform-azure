# Terraform Bootstrap

## Purpose

The bootstrap module establishes the minimum trusted foundation required for Terraform to manage the Azure Enterprise Platform.

Terraform cannot use a remote backend until that backend exists.

This module solves the initial bootstrap problem by creating the Azure resources required to host Terraform remote state.

After bootstrap is complete, Terraform state is migrated from local storage into the Azure Storage backend and all subsequent infrastructure deployments use the remote backend.

This module is intentionally small.

Its responsibility is limited to establishing Terraform's operational foundation.

---

# Business Problem

Enterprise Terraform deployments require:

- Centralized state management
- Team collaboration
- State locking
- Disaster recovery
- Consistent infrastructure lifecycle management

Without a remote backend:

- Engineers maintain separate local state files
- Concurrent deployments become unsafe
- Infrastructure ownership becomes fragmented
- Disaster recovery becomes difficult
- State corruption becomes more likely

This module creates the minimum infrastructure required to solve those problems.

---

# Architecture

Bootstrap creates:

```
Resource Group
        │
        ▼
Storage Account
        │
        ▼
Private Blob Container
        │
        ▼
Terraform Remote State
```

Initially Terraform executes using local state.

After the storage backend is created, state is migrated into Azure Storage using:

```bash
terraform init -migrate-state
```

After migration, all future Terraform executions use the remote backend.

---

# Resources Created

This module creates:

- Azure Resource Group
- Azure Storage Account
- Private Blob Container for Terraform state

---

# Inputs

| Variable | Description |
|----------|-------------|
| `org_prefix` | Organization naming prefix |
| `location` | Azure region |
| `unique_suffix` | Ensures globally unique storage account naming |
| `account_tier` | Storage account performance tier |
| `account_replication_type` | Storage redundancy strategy |
| `https_traffic_only_enabled` | Enforce encrypted transport |

---

# Outputs

The module exposes only information required by downstream platform components.

- Resource Group Name
- Storage Account Name
- Storage Account Resource ID
- Blob Container Name

Sensitive information such as storage keys, connection strings, or credentials are intentionally **not** exposed.

---

# Security Decisions

This module intentionally implements several security controls.

- HTTPS-only communication
- Private blob container
- Terraform state isolated from application workloads
- Standardized naming
- Standardized tagging

Future iterations will include:

- Blob Versioning
- Soft Delete
- Private Endpoint
- Private DNS
- Customer Managed Keys
- Diagnostic Settings

These enhancements will be introduced as the platform networking and security architecture evolves.

---

# Deployment Flow

Bootstrap is executed only during initial platform setup.

```
Local Terraform State
        │
        ▼
Bootstrap Infrastructure
        │
        ▼
Azure Storage Backend
        │
        ▼
terraform init -migrate-state
        │
        ▼
Remote Terraform State
```

After migration, all infrastructure deployments use the centralized backend.

---

# Future Architecture

The long-term architecture replaces temporary bootstrap access with enterprise automation.

```
GitHub Actions
        │
OIDC Federation
        │
Microsoft Entra ID
        │
Short-lived Token
        │
Self-hosted Runner
        │
Private Endpoint
        │
Terraform State
```

This removes long-lived credentials while ensuring the Terraform backend remains privately accessible.

---

# Design Principles

This module follows several architectural principles established in earlier ADRs.

- Humans provide intent.
- Terraform derives organizational standards.
- Minimize shared operational risk.
- Least privilege by default.
- Security through defense in depth.
- Bootstrap remains intentionally small.
- The secure path should become the easiest path.

---

# Operational Notes

Bootstrap should be executed once for a new platform environment.

Subsequent platform changes should occur through the enterprise CI/CD pipeline rather than repeated bootstrap execution.

Bootstrap infrastructure should be treated as highly privileged because compromise of Terraform state can impact the entire platform.

## Technical Debt

The current bootstrap implementation intentionally uses a temporary public endpoint to enable initial Terraform state migration.

Future platform iterations will:

- Restrict bootstrap access to approved IP addresses.
- Introduce Private Endpoints.
- Introduce Private DNS.
- Transition CI/CD to GitHub OIDC with self-hosted runners.
- Disable public network access completely.