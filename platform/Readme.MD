Developer
    |
    v
SOG Platform API
    |
    +-- Authenticate developer
    +-- OPA authorization
    +-- Validate workload intent
    |
    v
ChangeSetAssembler
    |
    v
12 Generated Infrastructure Files
    |
    v
GitHub App
    |
    +-- Create branch
    +-- Commit files
    +-- Open Pull Request
    |
    v
Platform Engineering Review
    |
    v
GitHub Actions
    |
    v
Terraform + Argo CD
    |
    v
Azure / AKS


Auth model

Developer
    |
    | Login
    v
Trusted Identity Provider
    |
    | Signed JWT
    v
sogctl / Developer Portal
    |
    | Authorization: Bearer <token>
    v
Platform API
    |
    | Verify signature
    | Verify issuer
    | Verify audience
    | Verify expiration
    v
Trusted Developer Identity
    |
    v
OPA