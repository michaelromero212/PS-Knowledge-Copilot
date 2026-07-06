# Incident Management Guide
> Source: Confluence — IT Service Management Space

## What Is an Incident
An **incident** is any unplanned interruption to a service or reduction in its quality. The goal of incident management is to restore normal service operation as quickly as possible while minimizing business impact.

## Priority Matrix
Priority is derived from **Impact × Urgency**:
- **P1 (Critical)**: Enterprise-wide outage or a critical service down for many users. Target response: 15 minutes. Target resolution: 4 hours.
- **P2 (High)**: A major service degraded, or a critical function affecting a department. Response: 30 minutes. Resolution: 8 hours.
- **P3 (Moderate)**: Single user or small group impacted, workaround available. Response: 4 hours. Resolution: 2 business days.
- **P4 (Low)**: Minor issue or request with no immediate business impact. Response: 1 business day. Resolution: 5 business days.

## Incident Lifecycle
1. **Identification & Logging**: Capture the incident via the service portal, email, or monitoring alert. Record a clear summary, affected service, and configuration items (CIs).
2. **Categorization**: Assign category and subcategory so routing and reporting are accurate.
3. **Prioritization**: Apply the impact/urgency matrix.
4. **Investigation & Diagnosis**: Reproduce, gather logs, and identify the probable cause.
5. **Resolution & Recovery**: Apply a fix or workaround and confirm service restoration with the user.
6. **Closure**: Confirm resolution, record the resolution code, and capture a knowledge article if reusable.

## Key Metrics
- **MTTR (Mean Time To Resolve)**: Average time from logging to resolution. Track by priority.
- **MTTA (Mean Time To Acknowledge)**: How quickly a responder picks up the ticket.
- **First Contact Resolution (FCR)**: Percentage resolved at the service desk without escalation.
- **Reopen rate**: High reopen rates signal premature closures.

## Best Practices
- Never resolve a ticket without confirming with the requester.
- Link recurring incidents to a **problem record** for root-cause analysis.
- Keep the customer updated at every status change — communication reduces escalations more than speed alone.
