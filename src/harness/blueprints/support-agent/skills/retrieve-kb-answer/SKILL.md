---
name: retrieve-kb-answer
description: Search the project KB and return either a direct answer with citations or "no high-confidence match".
version: 1.0.0
when_to_use: After classify-intent returns `question`.
inputs:
  - { name: question, type: string, required: true }
  - { name: confidence_threshold, type: number, required: false, description: "Default: 0.7" }
outputs:
  - { name: answer, type: object, description: "{reply, citations[]} or {reply: null, reason: 'low_confidence'}" }
---

# Retrieve KB Answer

## Steps

1. Run vector + keyword hybrid search over the project KB (likely under
   `docs/`, `kb/`, or the README + CONTRIBUTING).
2. Compute reranker confidence. If ≥ `confidence_threshold`, draft a
   reply that cites every claim by source filename + section anchor.
3. If below threshold, return `{reply: null, reason: "low_confidence",
   topics: [...]}` so the next step files a ticket instead.
4. **Never** guess: if the KB doesn't cover it, that's a ticket, not a wing-it.

## Output shape

```jsonc
{
  "reply": "...",                          // or null
  "citations": [{"source": "docs/x.md#hdr", "snippet": "..."}],
  "confidence": 0.84,
  "reason": null                            // or "low_confidence"
}
```

## Failure modes

- Citing a doc you didn't actually retrieve.
- Suppressing low confidence so the answer ships unticketed (looks
  productive; produces angry follow-ups).
- Replying with the user's question rephrased — say nothing rather than
  hallucinating an answer.
