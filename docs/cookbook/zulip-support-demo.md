# Zulip + Support demo

A customer-support agent for the `zulip/zulip` repo's own issue tracker, with SLA + escalation lineage.

## Reproduce

```bash
cd /tmp
git clone https://github.com/zulip/zulip.git
cd zulip
git checkout <pinned-SHA>

uvx harness-kit init --no-llm --blueprint support-agent
```

## What gets written

- `AGENTS.md` with the support loop (intent → KB → ticket → escalate)
- `SOUL.md` setting the "warm but brief, no corporate cliché" voice — appropriate for an OSS community
- `TOOLS.md` recommending `github` (Zulip's tracker), `postgres`, `slack`, and the SLA matrix
- `MEMORY.md` defining `conversation` + `ticket-history` schemas
- `SKILLS/classify-intent/` — categorize inbound issues
- `SKILLS/retrieve-kb-answer/` — search Zulip's own docs first
- `SKILLS/file-ticket/` — create a GitHub Issue with proper lineage
- `SKILLS/escalate-if-unresolved/` — Slack ping when SLA breached
- Adapter files for Claude Code, Cursor, Continue, Windsurf, Codex

## Why this demo

- Large Django app with a real ticket model — exercises support-agent end-to-end
- harness picks up existing issue templates as memory schema reference
- `SOUL.md` reflects Zulip's known open-source community tone
- The validator `ticket_lineage` enforces the same convention Zulip itself prefers — explicit "originating message" backlink on every triage
