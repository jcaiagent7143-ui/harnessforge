# Airflow + Workflow

`apache/airflow` × `workflow-agent` blueprint. Meta-poetic.

```bash
./run.sh
HERO_AIRFLOW_SHA=abc1234 ./run.sh
```

What you get:

- `AGENTS.md` — workflow loop (decompose → call → check → log → next)
- `SOUL.md` — "operational, low-drama" voice for an infrastructure project
- `TOOLS.md` — filesystem, fetch, shell, github, postgres + tool-log contract
- `MEMORY.md` — tool log + skill-derived heuristics
- `SKILLS/{decompose-task, call-tool-with-retry, check-result}/`
- Five IDE adapters

The `idempotent` validator enforces the same property Airflow itself depends on for retries.

See [Cookbook: Airflow + Workflow demo](../../../docs/cookbook/airflow-workflow-demo.md).
