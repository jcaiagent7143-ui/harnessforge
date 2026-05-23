---
name: file-ticket
description: Create a ticket with intent, priority, and lineage back to the originating conversation turn.
version: 1.0.0
when_to_use: After retrieve-kb-answer returns low confidence OR intent is bug/feature/billing.
inputs:
  - { name: conversation_id, type: string, required: true }
  - { name: intent, type: string, required: true }
  - { name: title, type: string, required: true }
  - { name: description, type: string, required: true }
  - { name: turn_index, type: int, required: true, description: "Originating message index." }
outputs:
  - { name: ticket, type: object, description: "{ticket_id, priority, sla_due_at, lineage}" }
---

# File Ticket

## Steps

1. **Pick priority** from the SLA matrix in `TOOLS.md`:
   - P0 — production down for many users
   - P1 — feature broken for one customer; or paid-plan blocker
   - P2 — bug with workaround, or feature on a roadmap
   - P3 — nice-to-have or general feedback
2. **Compute `sla_due_at`** = now + first-response SLA for the priority.
3. **Write lineage** — `[{turn: <turn_index>, message_id: <id>}]`. The
   validator `check_ticket_lineage` will reject orphan tickets.
4. **Create** via the ticket-tracker MCP (`github`, `linear`, etc.). Use
   labels: `intent:<intent>`, `priority:<P0|P1|...>`.
5. **Return** the ticket object. Persist to `ticket_history` per
   `MEMORY.md` layer 2.

## Failure modes

- Filing without lineage → validator fails the run.
- Defaulting priority to P2 to avoid escalation paperwork.
- Creating duplicate tickets — search open tickets with the same intent
  + originating user first.
