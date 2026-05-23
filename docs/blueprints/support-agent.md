# Support agent

Customer support automation: intent classification → KB retrieval → ticket creation with SLA + escalation lineage.

## When to use

You're building a support/help-desk agent that takes inbound messages,
either answers them from the knowledge base or files a ticket, and
never loses the conversation lineage.

## The loop

```
classify intent → search KB → either answer or file a ticket → log lineage → maybe escalate
```

## What gets generated

| File | Role |
|---|---|
| `AGENTS.md` | Support loop + SLA + escalation rules |
| `SOUL.md` | "Warm but brief, no corporate cliché" voice |
| `TOOLS.md` | Ticketing + KB + Slack MCP recommendations + SLA matrix |
| `MEMORY.md` | Three layers (session conversation / tickets / skill metrics) |
| `SKILLS/classify-intent/` | question / bug / feature / billing / other |
| `SKILLS/retrieve-kb-answer/` | KB search with confidence threshold |
| `SKILLS/file-ticket/` | Lineage-preserving ticket creation |
| `SKILLS/escalate-if-unresolved/` | SLA-driven escalation with notify-user |
| `scripts/test_task.sh` | Inbound message replay |
| `scripts/verify_output.py` | Reply / ticket lineage check |

## Validators

| Validator | What it checks |
|---|---|
| `structure` | Every blueprint-generated file present and parses |
| `ticket_lineage` | Every created ticket has `conversation_id` + non-empty `lineage` |
| `sla` | Every ticket priority is in `{P0, P1, P2, P3}` + `sla_due_at` populated |

## SLA matrix (also rendered into TOOLS.md)

| Priority | First-response SLA | Resolve SLA |
|----------|--------------------|-------------|
| P0       | 15 min             | 4 hr        |
| P1       | 1 hr               | 1 day       |
| P2       | 4 hr               | 3 days      |
| P3       | 1 day              | 1 week      |

## Memory schemas

- `conversation` — message log with intent + KB consultation history
- `ticket-history` — durable ticket records with required lineage

## Hero demo

[Zulip + support cookbook](../cookbook/zulip-support-demo.md) shows this blueprint on `zulip/zulip`.
