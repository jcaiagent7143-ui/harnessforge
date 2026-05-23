---
name: escalate-if-unresolved
description: Escalate any open ticket past its SLA to a human, preserving lineage.
version: 1.0.0
when_to_use: Run on a schedule (every 5 minutes via cron) OR on every inbound message in the same conversation.
inputs:
  - { name: ticket_id, type: string, required: true }
outputs:
  - { name: escalation, type: object, description: "{escalated_to, channel, ts, status}" }
---

# Escalate if Unresolved

## Steps

1. Load the ticket. If `status != open` or `now() < sla_due_at`, return
   `{status: "no-op"}`.
2. **Pick the escalation channel**: Slack channel from `TOOLS.md`
   (`#support-escalations` by default).
3. **Send** the escalation message with: ticket id, originating
   conversation link, priority, time over SLA, summary, lineage.
4. **Update** the ticket: `status = "escalated"`, `escalated_at = now`,
   `escalated_to = <channel/user>`.
5. **Notify the user** in the original conversation thread: *"This is
   taking longer than our SLA — a human is now reviewing. Ticket
   `<id>`."* Honest, no hedging.

## Failure modes

- Escalating without notifying the user (they think they're forgotten).
- Re-escalating an already-escalated ticket on every cron tick.
- Losing lineage — the escalation message must include the link back to
  the original conversation.
