# Change Management Process
> Source: Confluence — IT Service Management Space

## Purpose
Change management ensures that changes to IT services are recorded, assessed, approved, and implemented in a controlled way that minimizes risk and disruption.

## Change Types
- **Standard change**: Pre-approved, low-risk, repeatable (e.g., adding a user to a group, routine patching). No CAB approval required — governed by a change model.
- **Normal change**: Requires risk assessment and approval by the Change Advisory Board (CAB) before implementation.
- **Emergency change**: Needed to resolve a major incident or prevent one. Reviewed by the Emergency CAB (ECAB) with expedited approval and retrospective documentation.

## Risk Assessment
Score each change on likelihood of failure and potential business impact. A typical risk grid classifies changes as **low, medium, or high** risk. High-risk changes require a detailed implementation plan, a tested rollback plan, and a defined maintenance window.

## The Change Advisory Board (CAB)
- Meets on a regular cadence (often weekly) to review normal changes.
- Evaluates business justification, risk, resource availability, and scheduling conflicts.
- Checks the **forward schedule of change (FSC)** for collisions with other changes or freeze periods.

## Required Fields for a Change Request
1. Description and business justification.
2. Affected configuration items (CIs) and services.
3. Implementation plan with steps and owners.
4. **Rollback / back-out plan** — mandatory for all normal and emergency changes.
5. Test evidence and validation criteria.
6. Scheduled window and communication plan.

## Best Practices
- Always require a tested rollback plan — an unrecoverable change is an incident waiting to happen.
- Use change freezes during peak business periods (fiscal close, major events).
- Conduct a **post-implementation review (PIR)** for failed or high-risk changes to feed lessons learned back into change models.
