# ServiceNow Workflow Tips
> Source: #itsm-platform Slack channel — compiled from team discussions

## Flow Designer vs. Legacy Workflow
- Build all **new** automations in **Flow Designer**, not the legacy Workflow Editor. Flow Designer is the supported path and is easier to debug with the execution log.
- Use **subflows** for logic you reuse across multiple catalog items (e.g., manager approval, license check) instead of copy-pasting.

## Catalog Items & Record Producers
- Use a **record producer** when you want a friendly form that creates a record on a table (incident, HR case).
- Use a **catalog item** for fulfillment workflows that need tasks, approvals, and a request (REQ/RITM) structure.
- Keep variable sets DRY: shared variables (cost center, region) belong in a reusable **variable set**.

## Assignment Rules
- Prefer **assignment rules** and **data lookup rules** over hard-coded scripts for routing. They are configurable by admins without code.
- For round-robin distribution across an assignment group, use **advanced work assignment (AWA)** rather than custom scripts.

## Approvals
- Model approvals as flow actions with clear approval fields. Avoid nesting more than two levels of approval — it slows fulfillment and frustrates requesters.
- Always set an **approval timeout / reminder** so requests don't stall on an out-of-office approver.

## Common Pitfalls
- Don't run heavy logic in **business rules** that fire on every update — move it to scheduled jobs or flows.
- Test in a **sub-production instance** and promote with **update sets** or the pipeline; never build directly in production.
- Watch for **ACL** gaps: a form that works for admins may silently fail for end users lacking read/write access.
