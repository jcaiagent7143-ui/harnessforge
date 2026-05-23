# RAG Agent blueprint

Retrieval-augmented question-answering with citation enforcement.

## What this blueprint generates

- `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md` — the universal harness files
- `SKILLS/chunk-and-embed/`, `SKILLS/retrieve-and-rerank/`, `SKILLS/answer-with-citations/`, `SKILLS/eval-recall-precision/` — anthropics/skills-compatible
- `scripts/test_task.sh` — sample RAG question runner
- `scripts/verify_output.py` — citation + Pydantic-schema check

## When to use

Your project will answer questions grounded in a document corpus
(docs, knowledge base, manuals, internal wiki). You want every claim
the agent makes to cite a retrieved chunk.

## Validators

- `structure` — every generated file is present and parses
- `citations` — every factual claim cites a `chunk_id`
- `schema`   — Pydantic output schema validates against a sample answer

Run with `harness verify` after bootstrapping.
