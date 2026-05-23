# Workflow Agent blueprint

Orchestrate tools + APIs to complete multi-step tasks. The generic default
blueprint — use this when none of the more specialized ones (rag-agent,
support-agent) fit cleanly.

## What this blueprint generates

- `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md`
- `SKILLS/decompose-task`, `SKILLS/call-tool-with-retry`, `SKILLS/check-result`
- `scripts/test_task.sh`, `scripts/verify_output.py`

## When to use

You're building a *general* multi-step automation: ingest something, call
APIs, write somewhere, notify someone. Think: Zapier-with-judgment, or a
custom internal tool that needs to be reliable.

## Validators

- `structure`  — every file present
- `tool_log`   — every tool call has args + result recorded
- `idempotent` — final step is marked idempotent (safe to retry)
