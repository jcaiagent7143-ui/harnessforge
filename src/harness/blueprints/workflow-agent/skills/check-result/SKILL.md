---
name: check-result
description: Verify the expected effect of a step actually happened before moving to the next.
version: 1.0.0
when_to_use: After every step in the plan.
inputs:
  - { name: step, type: object, required: true, description: "The plan entry, with expected_effect." }
  - { name: result, type: object, required: true, description: "Output of call-tool-with-retry." }
outputs:
  - { name: verdict, type: object, description: "{ok, evidence?, mismatch?}" }
---

# Check Result

## Steps

1. Read `step.expected_effect` — what observable thing should be true now?
2. Probe for it independently: re-read the file, GET the API endpoint,
   query the DB. Don't trust the call's return value alone.
3. If observed matches expected → `ok=true` + cite the evidence.
4. If not → `ok=false` with the specific mismatch. Decide: retry this step,
   roll back, or escalate to the user.

## Output shape

```jsonc
{
  "ok": true,
  "evidence": "GET /things/42 returned 200 with name='new-thing'"
}
// or
{
  "ok": false,
  "mismatch": "expected file out.json present; got ENOENT",
  "action": "retry-step"
}
```

## Failure modes

- Trusting the tool's own success signal — many APIs return 200 + body
  saying "queued" while the side effect never lands.
- Re-checking via the same code path that just wrote — use an independent probe.
- Treating "looks ok" as "is ok"; the verdict is binary.
