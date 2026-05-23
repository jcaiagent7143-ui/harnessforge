---
name: classify-intent
description: Classify an inbound support message into question / bug / feature / billing / other.
version: 1.0.0
when_to_use: Step 1 of every inbound. Output drives every downstream branch.
inputs:
  - { name: message, type: string, required: true }
outputs:
  - { name: intent, type: string, description: "question | bug | feature | billing | other" }
  - { name: confidence, type: number, description: "0.0–1.0 self-reported confidence." }
---

# Classify Intent

## Steps

1. Read the message.
2. If it asks a how-to or what-is question → `question`.
3. If it describes broken behavior, error, or unexpected output → `bug`.
4. If it asks for a new capability → `feature`.
5. If it's about pricing, invoices, refunds, plan changes → `billing`.
6. Otherwise → `other`.
7. Return `confidence` honestly. Below 0.5 → escalate to a human classifier
   rather than guessing.

## Failure modes

- Treating "this is slow" as `question` (it's a `bug`).
- Treating refund requests as `other` to dodge billing escalation rules.
- Stacking multiple intents into one ticket — split them.
