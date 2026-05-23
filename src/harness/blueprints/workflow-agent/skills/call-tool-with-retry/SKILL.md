---
name: call-tool-with-retry
description: Call one tool, retry with exponential backoff on transient errors, log every attempt.
version: 1.0.0
when_to_use: Every tool invocation goes through this — never call a tool directly.
inputs:
  - { name: tool, type: string, required: true }
  - { name: args, type: object, required: true }
  - { name: max_retries, type: int, required: false, description: "Default: 3." }
  - { name: idempotent, type: bool, required: false, description: "Default: false (refuse to retry on ambiguous failure)." }
outputs:
  - { name: result, type: object, description: "{ok, value?, error?, attempts}" }
---

# Call Tool with Retry

## Steps

1. **Record the attempt** in the tool log BEFORE calling — so a crash mid-call still leaves a trail.
2. **Call the tool** with the args.
3. On success: record `ok=true`, return.
4. On error: classify (transient vs. terminal). Backoff: `2^attempt` seconds, cap 30s.
5. Retry up to `max_retries` only if `idempotent=true` OR the error is provably terminal-safe-to-retry
   (e.g. `429` rate limit, `503` upstream).
6. On final failure: record `ok=false` with the error, return.

## Output shape

```jsonc
{
  "ok": true,
  "value": { ... },
  "attempts": 1
}
// or
{
  "ok": false,
  "error": "503 upstream timeout",
  "attempts": 3
}
```

## Failure modes

- Retrying a non-idempotent POST → duplicate side effects.
- Logging *after* the call → crash data loss.
- Treating all 4xx as terminal — `408`, `429` are transient.
- Sleeping a literal `time.sleep(30)` in a single-threaded loop → blocks the
  whole pipeline. Use async sleep / a job queue.
