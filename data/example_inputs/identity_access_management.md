# Identity & Access Management (IAM)
> Source: Confluence — Security & Compliance Space

## Core Principles
- **Least privilege**: Grant users the minimum access needed to do their job, and nothing more.
- **Separation of duties**: No single person should control an entire high-risk process (e.g., the person who requests access should not also approve it).
- **Just-in-time (JIT) access**: Grant elevated/privileged access temporarily and revoke it automatically when the task is done.

## Role-Based Access Control (RBAC)
- Assign permissions to **roles**, then assign roles to users — never assign permissions to individuals directly.
- Keep roles aligned to job functions (e.g., "Service Desk Analyst", "Network Engineer") and review them regularly.
- Avoid **role explosion**: too many narrow roles becomes as hard to manage as no roles at all.

## Provisioning & Deprovisioning
1. **Onboarding**: Trigger access from an authoritative HR source. Use birthright roles for baseline access (email, intranet, laptop).
2. **Changes**: When someone moves teams, remove old access as you add new — "access accretion" is a top audit finding.
3. **Offboarding**: Disable accounts within hours of termination. Automate this from the HR feed; manual offboarding is error-prone and a security risk.

## Authentication
- Enforce **multi-factor authentication (MFA)** for all users, and phishing-resistant MFA (FIDO2/passkeys) for privileged accounts.
- Use **single sign-on (SSO)** via SAML or OIDC to centralize authentication and reduce password sprawl.

## Access Reviews
- Conduct **periodic access certifications** (quarterly for privileged, annually for standard). Managers attest that each report still needs their access.
- Log and monitor privileged access; alert on unusual activity such as off-hours admin logins.

## Best Practices
- Automate deprovisioning from the HR system of record — it closes the biggest access-risk gap.
- Never share service-account credentials in tickets or chat; use a secrets vault.
