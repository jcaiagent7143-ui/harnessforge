---
name: chunk-and-embed
description: Split source documents into stable-id chunks and embed them into the configured vector store.
version: 1.0.0
when_to_use: Before any retrieval is possible — run once per source change.
inputs:
  - { name: docs_dir, type: path, required: true, description: "Directory of source documents (.md, .txt, .pdf)." }
  - { name: chunk_size_chars, type: int, required: false, description: "Default: 1500." }
  - { name: overlap_chars, type: int, required: false, description: "Default: 200." }
outputs:
  - { name: chunks_index, type: path, description: "JSONL of chunks written; consumed by retrieve-and-rerank." }
---

# Chunk and Embed

## Steps

1. **Walk `docs_dir`** for supported extensions (`.md`, `.txt`, `.pdf`,
   `.rst`). Skip anything in `MEMORY.md`'s forbidden list.
2. **Split** each document into ~`chunk_size_chars` chunks with
   `overlap_chars` of overlap. Prefer paragraph boundaries; never split
   mid-sentence.
3. **Compute a stable `chunk_id`** = sha256 of `(source_path + offset + text)`,
   truncated to 12 chars. This is what the answer cites — it must not change
   if the same content is re-ingested.
4. **Embed** with the configured model (default `text-embedding-3-small`).
5. **Upsert** into the vector store (Qdrant/Chroma/pgvector) keyed by `chunk_id`.
6. **Write `chunks_index.jsonl`** with one record per chunk: `{chunk_id,
   source, offset, text, metadata}`. This is what the verifier and the
   reranker read.

## Validation

After running, `harness verify --check structure` should pass. A
non-empty `chunks_index.jsonl` proves you ran. If the same content is
re-ingested, `chunk_id`s must be stable (use a fixture test).

## Failure modes to avoid

- **chunk_id drift** — recomputing on slightly different text breaks every
  prior citation. Make the hash include the *normalized* text (collapse
  whitespace) but never the timestamp.
- **embedding model change without re-indexing** — versions the model and
  records it in `chunks_index.jsonl` so the reranker can detect mismatch.
- **silent skip on parse errors** — log every file you couldn't read.
