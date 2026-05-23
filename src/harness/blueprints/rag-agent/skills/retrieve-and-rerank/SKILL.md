---
name: retrieve-and-rerank
description: Retrieve top-k chunks for a question, rerank with a cross-encoder, return the top-n with scores.
version: 1.0.0
when_to_use: First step of answering any user question.
inputs:
  - { name: question, type: string, required: true }
  - { name: top_k, type: int, required: false, description: "Initial recall set. Default: 20." }
  - { name: top_n, type: int, required: false, description: "After rerank. Default: 5." }
outputs:
  - { name: chunks, type: array, description: "[{chunk_id, source, text, score}], length ≤ top_n" }
---

# Retrieve and Rerank

## Steps

1. **Embed the question** with the same model used during ingestion.
2. **Vector search** for `top_k` candidates by cosine similarity.
3. **Rerank** with a cross-encoder (e.g. `bge-reranker-base` or LLM-judge
   prompt) — the bi-encoder score is recall, the cross-encoder score is
   precision.
4. **Return the top `top_n`** with their reranker score.
5. **Log retrieval** to session memory (`retrieved_chunks` per turn) so
   the validator can confirm cited chunks were actually retrieved.

## Validation

`harness verify --check citations` confirms every chunk cited in the
answer is in the session's `retrieved_chunks` list. If you skip the
session-memory log step, this validator will fail every run.

## Failure modes to avoid

- **Skipping the rerank** — bi-encoder alone returns plausible-but-irrelevant
  chunks; the answerer then hallucinates a justification.
- **Returning chunks the user can't see** — if a chunk was indexed from a
  forbidden path, the retriever must skip it. Check `MEMORY.md`.
- **No empty-result handling** — if `top_n == 0`, the answerer must say so;
  don't invent.
