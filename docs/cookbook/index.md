# Cookbook

End-to-end demos on real public repos. Each demo:

1. Clones a real OSS project at a pinned SHA
2. Runs `harness init --no-llm` against it
3. Shows the generated tree
4. Runs `harness verify` to confirm everything passes

The reproducibility scripts live under `examples/hero/` in the repo.

## Demos

- [FastAPI + RAG demo](fastapi-rag-demo.md) — `fastapi/full-stack-fastapi-template` × `rag-agent`
- [Zulip + Support demo](zulip-support-demo.md) — `zulip/zulip` × `support-agent`
- [Airflow + Workflow demo](airflow-workflow-demo.md) — `apache/airflow` × `workflow-agent`
