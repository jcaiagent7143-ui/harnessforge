# Workflow agent

Orchestrate tools + APIs to complete multi-step tasks. The generic default
blueprint — use this when none of the more specialized ones fit cleanly.

## When to use

You're building a *general* multi-step automation: ingest something, call APIs, write somewhere, notify someone. Think: Zapier-with-judgment, or a custom internal tool that needs to be reliable.

## The loop

```
decompose → for each step: call tool with retry → check result → log → next
```

## What gets generated

| File | Role |
|---|---|
| `AGENTS.md` | Workflow loop + conventions + forbidden lists |
| `SOUL.md` | "Operational, low-drama execution layer" voice |
| `TOOLS.md` | Per-tool docs + tool-call logging contract |
| `MEMORY.md` | Per-task tool log + skill-derived heuristics |
| `SKILLS/decompose-task/` | Plan generator with idempotency markers |
| `SKILLS/call-tool-with-retry/` | Exponential-backoff + idempotency check |
| `SKILLS/check-result/` | Independent observation of expected effect |
| `scripts/test_task.sh` | Sample task replay |
| `scripts/verify_output.py` | Plan + tool log + idempotency check |

## Validators

| Validator | What it checks |
|---|---|
| `structure` | Every blueprint-generated file present and parses |
| `tool_log` | Every plan step that uses a tool has a `tool_log` entry |
| `idempotent` | Final plan step is marked `idempotent: true` (safe to retry) |

## Recommended MCP servers

- `filesystem` — read/write project files
- `fetch` — HTTP requests
- `shell` — run commands (refuses forbidden_commands)
- `github` — PRs / issues / actions
- `postgres` — read-only DB queries

## Memory schemas

- `conversation` — run_id + task + plan + tool_log + final_status + idempotent_marker

## Hero demo

[Airflow + workflow cookbook](../cookbook/airflow-workflow-demo.md) shows this blueprint on `apache/airflow`.
