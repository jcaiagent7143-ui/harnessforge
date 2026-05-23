# Airflow + Workflow demo

A workflow agent for `apache/airflow` — meta-poetic, since Airflow itself is a workflow engine.

## Reproduce

```bash
cd /tmp
git clone https://github.com/apache/airflow.git
cd airflow
git checkout <pinned-SHA>

uvx harness-kit init --no-llm --blueprint workflow-agent
```

## What gets written

- `AGENTS.md` with the workflow loop (decompose → call → check → log → next)
- `SOUL.md` setting the "operational, low-drama" voice — appropriate for an infrastructure project
- `TOOLS.md` recommending `filesystem`, `fetch`, `shell`, `github`, `postgres` + the tool-call logging contract
- `MEMORY.md` defining `tool_log` + skill-derived heuristics
- `SKILLS/decompose-task/` — plan generator with idempotency markers
- `SKILLS/call-tool-with-retry/` — exponential-backoff retry
- `SKILLS/check-result/` — independent verification of expected effects
- Adapter files for Claude Code, Cursor, Continue, Windsurf, Codex

## Why this demo

- High recognition value — every data engineer knows Airflow
- Correctly recommends Airflow-aware MCPs through the catalog
- The `idempotent` validator enforces the same property Airflow itself depends on for retries
- Demonstrates that "workflow" is not just a fallback — it's a real production pattern

## Validators

After `init`:

```bash
$ harness verify --json
{
  "blueprint": "workflow-agent",
  "checks": [
    {"name": "structure",  "status": "pass"},
    {"name": "tool_log",   "status": "skipped"},
    {"name": "idempotent", "status": "skipped"}
  ],
  "summary": {"total": 3, "passed": 1, "failed": 0}
}
```

The `tool_log` and `idempotent` checks skip cleanly until an agent actually produces a `/tmp/airflow-workflow-output.json`. Once your coding agent runs a workflow, the validators score it against the contract.
