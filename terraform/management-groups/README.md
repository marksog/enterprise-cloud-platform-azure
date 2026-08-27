# Azure Management Groups

## Purpose

This Terraform configuration creates the enterprise Azure Management Group hierarchy used to organize subscriptions and apply governance consistently across the platform.

Management Groups provide a governance layer above Azure subscriptions.

They allow the organization to:

- Apply policy at the appropriate organizational scope
- Inherit governance controls across subscriptions
- Separate workloads with different risk profiles
- Apply RBAC at organizational boundaries
- Reduce duplicated policy assignments
- Reduce configuration drift
- Support future acquisitions and organizational growth

---

## Architecture

The current hierarchy is:

```text
Enterprise
├── Platform
├── Production
│   └── Regulated
├── Non-Production
├── Sandbox
└── Acquisitions