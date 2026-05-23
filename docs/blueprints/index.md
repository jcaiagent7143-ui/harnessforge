# Blueprints

A blueprint is a reusable agent pattern. Each blueprint ships:

- A `blueprint.yaml` spec (metadata + file list + validators)
- Jinja2 templates for the universal harness files (`AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md`)
- Skill bundles in [`anthropics/skills`](https://github.com/anthropics/skills) format
- Python validator modules
- Memory JSON Schemas
- An eval question set

v0.1 ships three:

| Blueprint | Doc |
|---|---|
| `rag-agent` | [RAG agent](rag-agent.md) |
| `support-agent` | [Support agent](support-agent.md) |
| `workflow-agent` | [Workflow agent](workflow-agent.md) |

v0.2 will add `sales-agent`, `browser-agent`, `finance-agent`.

## Pick a blueprint

```bash
harness blueprint list           # see installed
harness blueprint show rag-agent # full spec
harness init --blueprint rag-agent
```

## Recommendation heuristic

If you don't pass `--blueprint`, harness recommends:

- **`rag-agent`** when the repo has vector-store deps (langchain, qdrant, chroma, pinecone, weaviate, faiss) or "rag" / "docs" in the project name
- **`support-agent`** when the repo is a Django/Rails/Zulip/Discourse web-app or has "support" / "help" in the name
- **`workflow-agent`** otherwise (the generic default)

Explicit `--blueprint` always wins.

## Author your own

→ [Authoring a custom blueprint](../guides/custom-blueprint.md)
