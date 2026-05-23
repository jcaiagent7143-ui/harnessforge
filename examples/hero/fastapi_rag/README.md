# FastAPI + RAG

`fastapi/full-stack-fastapi-template` × `rag-agent` blueprint.

```bash
./run.sh                          # clones, inits, verifies
HERO_FASTAPI_SHA=abc1234 ./run.sh  # pin to a specific commit
```

What you get in the cloned repo:

- `AGENTS.md` — RAG loop tailored to the FastAPI template
- `SOUL.md` — "careful research assistant" voice
- `TOOLS.md` — qdrant, chroma, filesystem, fetch
- `MEMORY.md` — three-layer memory
- `SKILLS/{chunk-and-embed, retrieve-and-rerank, answer-with-citations, eval-recall-precision}/`
- Five IDE adapters: Claude Code, Cursor, Continue, Windsurf, Codex

After `init`, any coding agent (Claude Code, Cursor, etc.) opened in the cloned repo
picks up the harness automatically.

See [Cookbook: FastAPI + RAG demo](../../../docs/cookbook/fastapi-rag-demo.md).
