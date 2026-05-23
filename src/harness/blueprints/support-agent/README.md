# Support Agent blueprint

Intent → KB retrieval → ticket creation, with SLA + escalation lineage.

## What this blueprint generates

- `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md`
- `SKILLS/classify-intent`, `SKILLS/retrieve-kb-answer`, `SKILLS/file-ticket`, `SKILLS/escalate-if-unresolved`
- `scripts/test_task.sh` — sample inbound message handler
- `scripts/verify_output.py` — ticket + lineage check

## When to use

You're building a support / help-desk agent that takes inbound messages,
either answers them from the knowledge base or files a ticket, and never
loses the conversation lineage.

## Validators

- `structure`       — every generated file is present and parses
- `ticket_lineage`  — every created ticket links back to a conversation turn
- `sla`             — every priority value maps to a documented SLA
