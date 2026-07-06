# Endpoint Provisioning & Onboarding
> Source: #endpoint-engineering Slack channel — compiled from team discussions

## Zero-Touch Provisioning
- Use **zero-touch enrollment** (Autopilot for Windows, Automated Device Enrollment for macOS) so a new device configures itself on first boot from the corporate profile.
- Ship devices directly to the user; the device joins the MDM and pulls apps and policies without IT touching it.

## Mobile Device Management (MDM)
- Enroll every corporate endpoint in **MDM** to enforce baseline security: disk encryption, screen lock, OS patch level, and remote wipe.
- Group devices by role (developer, kiosk, executive) and apply configuration profiles per group.

## New-Hire Onboarding Checklist
1. HR triggers the onboarding request in the service portal on the signed start date.
2. Birthright access is provisioned automatically (identity, email, VPN, baseline apps).
3. Device is enrolled and shipped, or staged for pickup.
4. Role-specific software is delivered through the **self-service software catalog**, not manual installs.
5. Day-one checklist and knowledge articles are shared so the user can self-serve common tasks.

## Patch & Compliance
- Enforce a patch SLA: critical OS/security patches within 7 days, standard within 30.
- Report on **compliance drift** — devices that fall out of policy (unencrypted, out-of-date) should auto-remediate or be flagged.

## Common Pitfalls
- Don't rely on manual imaging — it's slow, inconsistent, and doesn't scale. Automate with MDM.
- Deprovision devices when staff leave: remote-wipe corporate data and reclaim licenses.
- Avoid local admin rights by default; grant elevation just-in-time through a privilege-management tool.
