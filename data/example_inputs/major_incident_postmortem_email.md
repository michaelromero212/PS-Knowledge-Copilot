# Major Incident Postmortem — Best Practices
> Source: Email digest — Reliability Engineering weekly

## When to Run a Postmortem
Run a **blameless postmortem** after every P1/major incident, and after any P2 that reveals a systemic weakness. The goal is learning and prevention, never blame.

## Blameless Culture
- Assume everyone acted reasonably with the information they had at the time.
- Focus on **systems and processes**, not individuals. "The deploy tool allowed an untested change" — not "Sam broke prod."
- Blameless reviews surface honest information; blame drives problems underground.

## Postmortem Structure
1. **Summary**: What happened, in two or three sentences.
2. **Impact**: Who and what was affected, for how long, and the business cost (users, revenue, SLA breach).
3. **Timeline**: Key events from detection to resolution, with timestamps.
4. **Root cause analysis (RCA)**: Use techniques like the **5 Whys** to move past symptoms to the underlying cause.
5. **What went well / what went poorly**: Honest reflection on detection, response, and communication.
6. **Action items**: Specific, owned, and dated corrective actions.

## Action Items
- Every action item needs an **owner** and a **due date**, and should be tracked to completion in the ticketing system.
- Prioritize actions that prevent recurrence or reduce detection time (MTTD) over cosmetic fixes.
- Review open postmortem actions in a recurring reliability meeting so they don't get dropped.

## Key Metrics to Discuss
- **MTTD (Mean Time To Detect)** and **MTTR (Mean Time To Resolve)**.
- Was the incident detected by monitoring or by a customer? Customer-detected outages indicate a monitoring gap.

## Best Practices
- Publish postmortems internally so other teams learn from them.
- Track recurring root causes across postmortems — a pattern is a signal to invest in a bigger fix.
