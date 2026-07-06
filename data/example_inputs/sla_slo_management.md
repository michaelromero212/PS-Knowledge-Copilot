# SLA, SLO & OLA Management
> Source: Google Drive — Service Delivery Shared Folder

## Definitions
- **SLA (Service Level Agreement)**: A commitment between the service provider and the customer (e.g., "P1 incidents resolved within 4 hours, 99.9% uptime").
- **SLO (Service Level Objective)**: The internal target that must be met to satisfy the SLA. SLOs are usually stricter than the SLA to leave a safety margin.
- **OLA (Operational Level Agreement)**: An internal agreement between teams that underpins an SLA (e.g., the network team responds to escalations within 30 minutes).
- **Error budget**: The allowable amount of failure. For a 99.9% availability SLO, the error budget is ~43 minutes of downtime per month.

## Designing SLAs
1. Base targets on **business impact**, not on what is technically easy to measure.
2. Define **service hours** (24×7 vs. business hours) and how the clock pauses (e.g., "awaiting customer" states stop the SLA timer).
3. Specify **measurement windows** (monthly, quarterly) and how breaches are calculated.

## Escalation
- Configure **SLA warnings** at 50% and 75% of the target so teams act before a breach.
- On breach, trigger an automatic escalation to the next support tier and notify the service owner.

## Reporting
- Track **SLA attainment %** per service and per priority.
- Report on **breaches with root cause** — a breach without an explanation erodes customer trust.
- Use error-budget burn rate to decide whether to slow feature changes and focus on reliability.

## Best Practices
- Don't promise 99.99% ("four nines") unless the underlying architecture and OLAs can support it.
- Review SLAs at least annually; business needs and service maturity change.
- Pausing the SLA clock during "awaiting customer" is standard and fair — document it clearly in the agreement.
