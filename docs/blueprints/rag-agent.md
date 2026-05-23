# RAG agent

Retrieval-augmented question answering with citation enforcement and recall/precision eval.

## When to use

Your project will answer questions grounded in a document corpus (docs,
knowledge base, manuals, internal wiki). You want every claim the agent
makes to cite a retrieved chunk.

## What gets generated

| File | Role |
|---|---|
| `AGENTS.md` | RAG-specific entry document (loop, conventions, definition of done) |
| `SOUL.md` | "Careful research assistant" voice |
| `TOOLS.md` | Recommended vector stores + retrieval MCP servers |
| `MEMORY.md` | Three-layer memory (session / corpus / skill-derived) |
| `SKILLS/chunk-and-embed/` | Ingestion + stable chunk_id assignment |
| `SKILLS/retrieve-and-rerank/` | Top-k retrieval + cross-encoder rerank |
| `SKILLS/answer-with-citations/` | Sentence-level citation enforcement |
| `SKILLS/eval-recall-precision/` | Eval set runner |
| `scripts/test_task.sh` | Sample question runner |
| `scripts/verify_output.py` | Citation + schema check |

## Validators

| Validator | What it checks |
|---|---|
| `structure` | Every blueprint-generated file is present and parses |
| `citations` | Every inline `[chunk_id]` matches an entry in `citations[]` (both directions) |
| `schema` | Sample answer JSON validates against the Pydantic shape |

## Recommended MCP servers

- `filesystem` — read corpus + write chunk index
- `fetch` — re-verify URL citations
- `postgres` — conversation + retrieval log persistence
- `qdrant` — vector store (>100k chunks)
- `chroma` — vector store (prototypes, <100k chunks)

## Memory schemas

- `conversation` — session messages + retrieved_chunks log
- `rag-chunks` — persistent chunk records (chunk_id, source, text, embedding, metadata)

## Eval

`eval/questions.yaml` ships with 4 sample questions and `min_recall: 0.7`, `min_precision: 0.5`. Replace these with corpus-specific questions before shipping.

## Hero demo

[FastAPI + RAG cookbook](../cookbook/fastapi-rag-demo.md) shows this blueprint on `fastapi/full-stack-fastapi-template`.
