# Hero demos

Reproducible end-to-end harnessforge demos against real public repos.

| Demo | Repo | Blueprint |
|---|---|---|
| `fastapi_rag/` | [fastapi/full-stack-fastapi-template](https://github.com/fastapi/full-stack-fastapi-template) | `rag-agent` |
| `zulip_support/` | [zulip/zulip](https://github.com/zulip/zulip) | `support-agent` |
| `airflow_workflow/` | [apache/airflow](https://github.com/apache/airflow) | `workflow-agent` |

Each demo has a `run.sh` that:

1. Clones the target repo at a **pinned SHA** into `/tmp`
2. Runs `harness init --no-llm --blueprint <name>`
3. Prints the generated tree
4. Runs `harness verify --json` to confirm everything passes

All deterministic — no LLM, no network, no auth.

Run any of them:

```bash
cd examples/hero/fastapi_rag && ./run.sh
```

CI runs all three on every push (see `.github/workflows/hero.yml`).
