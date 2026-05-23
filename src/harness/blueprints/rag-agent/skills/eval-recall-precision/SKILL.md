---
name: eval-recall-precision
description: Run the project's eval question set and report recall/precision against gold chunk_ids.
version: 1.0.0
when_to_use: Before merging changes that touch ingestion, retrieval, or reranker config.
inputs:
  - { name: eval_set, type: path, required: false, description: "Defaults to eval/questions.yaml under the blueprint." }
outputs:
  - { name: report, type: object, description: "Per-question recall/precision + aggregate." }
---

# Eval — Recall & Precision

## Steps

1. **Load** the eval set (`eval/questions.yaml` shipped with the blueprint).
   Each entry has `question`, `gold_chunk_ids`, optional `must_include_text`.
2. **For each question**, run `retrieve-and-rerank` → `answer-with-citations`.
3. **Score** against the gold:
   - **Recall** = |cited ∩ gold| / |gold|
   - **Precision** = |cited ∩ gold| / |cited|
4. **Aggregate** — report mean recall, mean precision, and per-question
   breakdown. Surface the bottom 3 questions for inspection.
5. **Fail** if mean recall < 0.7 or mean precision < 0.5 (configurable in
   `eval_set` metadata).

## Output shape

```jsonc
{
  "summary": {"mean_recall": 0.82, "mean_precision": 0.71, "n": 12},
  "per_question": [
    {"q": "...", "recall": 1.0, "precision": 0.75, "missing_gold": []}
  ]
}
```

## Validation

This skill *is* the validator for the retrieval layer. Run it from CI
after any change to `chunk-and-embed`, `retrieve-and-rerank`, or the
chunking config.

## Failure modes to avoid

- **Tuning the rerank threshold to pass eval, breaking real retrieval** —
  if eval recall jumps but production retrieval set shrinks, that's a
  red flag. Always report `top_n` distribution too.
- **Stale gold IDs** — if `chunk-and-embed` was rerun with new chunk_ids,
  the eval gold is stale. Re-author the eval set whenever ingestion
  changes meaningfully.
