# FastAPI + RAG demo

A retrieval-augmented Q&A agent over the `fastapi/full-stack-fastapi-template` docs.

## Reproduce

```bash
cd /tmp
git clone https://github.com/fastapi/full-stack-fastapi-template.git
cd full-stack-fastapi-template
git checkout <pinned-SHA>          # see examples/hero/fastapi_rag/run.sh

uvx harness-kit init --no-llm --blueprint rag-agent
```

## What gets written

The repo gains:

- `AGENTS.md` describing the RAG loop, conventions, and definition of done
- `SOUL.md` setting the "careful research assistant" voice
- `TOOLS.md` recommending qdrant + filesystem + fetch
- `MEMORY.md` defining the three-layer memory
- `SKILLS/chunk-and-embed/SKILL.md` for ingesting the FastAPI docs
- `SKILLS/retrieve-and-rerank/SKILL.md` for top-k + cross-encoder
- `SKILLS/answer-with-citations/SKILL.md` for citation-enforced answers
- `SKILLS/eval-recall-precision/SKILL.md` for the eval set runner
- Adapter files for Claude Code, Cursor, Continue, Windsurf, Codex

## Verify

```bash
harness verify --json
```

Should exit 0 with the `structure` check passing (citations + schema skip until an agent actually produces output).

## Now use it

Open the repo in Claude Code. Claude reads `.claude/CLAUDE.md`, learns the project type, the loop, the forbidden paths, and the citation contract — without any per-session prompting.

Or run Hermes in the same dir — Hermes reads `SOUL.md` and `SKILLS/` and starts with the same ground truth.

## Why this demo

- Multi-file output over a recognizable stack (FastAPI + React + Postgres)
- Demonstrates cross-agent interop: Claude Code, Cursor, OpenHarness all read the same `SKILLS/` and `AGENTS.md`
- Real corpus to ingest (the repo's own docs)
