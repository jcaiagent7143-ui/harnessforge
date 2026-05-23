---
name: answer-with-citations
description: Compose an answer that cites every factual claim by chunk_id, in a format the verifier understands.
version: 1.0.0
when_to_use: After retrieve-and-rerank returns ≥1 chunk; otherwise refuse.
inputs:
  - { name: question, type: string, required: true }
  - { name: chunks, type: array, required: true, description: "Output of retrieve-and-rerank." }
outputs:
  - { name: answer_json, type: object, description: "{answer, citations[], schema_version}" }
---

# Answer with Citations

## Steps

1. **For each sentence you write**, decide which retrieved chunk(s)
   support it. If none do, either: (a) don't write that sentence, or
   (b) flag it explicitly as not-from-corpus.
2. **Inline-cite** each factual sentence with the chunk_id in square
   brackets at the end: ``"Revenue grew 12% in Q3 [a1b2c3]."``
3. **Build the `citations` array** — one entry per cited chunk_id with
   the chunk's `source` and a 1-line snippet for the user to verify.
4. **Return** `{"answer": "...", "citations": [...], "schema_version": 1}`.
5. **If chunks contradict each other**, surface the contradiction — do
   not silently pick one.

## Output shape (Pydantic-validated)

```jsonc
{
  "schema_version": 1,
  "answer": "Revenue grew 12% in Q3 [a1b2c3]. Margins held flat [d4e5f6].",
  "citations": [
    {"chunk_id": "a1b2c3", "source": "reports/q3.md", "snippet": "..."},
    {"chunk_id": "d4e5f6", "source": "reports/q3.md", "snippet": "..."}
  ]
}
```

## Validation

`harness verify --check schema` validates the JSON; `--check citations`
cross-checks the inline tokens against the citations array (both
directions). Both must pass for the answer to ship.

## Failure modes to avoid

- **Fake citation IDs** — never invent `chunk_id`s. If you didn't see
  the chunk in retrieval output, you can't cite it.
- **Citation-orphaning** — listing a chunk_id in `citations[]` but never
  using it in the answer is also a failure (the verifier catches it).
- **One-citation-per-paragraph** — readers can't verify which sentence
  came from where. Cite per sentence.
