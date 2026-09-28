> **SYNTHETIC / DEMO DATA** for the fictitious company NorthPeak Digital Partners.

# Cybersecurity Capabilities

## Security Practices
NorthPeak's Cybersecurity & Risk group performs application security reviews (SAST/DAST tooling
integrated into CI), cloud configuration reviews, and third-party penetration test coordination
(tests are executed by an accredited external partner, not performed in-house).

## Identity & Access
Standard engagements implement SSO (SAML/OIDC) via providers such as Okta or Azure AD, with
role-based access control and least-privilege service accounts as a baseline requirement for any
production system NorthPeak deploys.

## Data Protection
NorthPeak designs systems with encryption at rest (AES-256) and in transit (TLS 1.2+) by default.
Key management typically uses the cloud provider's native KMS.

## Compliance Support
NorthPeak has supported clients preparing for SOC 2 Type II and ISO 27001 readiness assessments
by implementing required technical controls; NorthPeak itself has not published an independently
audited SOC 2 or ISO 27001 certificate for its own corporate environment, and this knowledge base
does not contain an auditor's report. Any RFP requirement asking for NorthPeak's own certified
audit report should be treated as an evidence gap requiring direct confirmation from NorthPeak's
compliance team.

## Explicit Non-Capability
NorthPeak does not hold FedRAMP authorization and does not currently support US federal
government workloads requiring FedRAMP Moderate/High baselines.
