---
name: classify-intent
description: Classify an inbound support message into question / bug / feature / billing / other.
version: 1.1.0
when_to_use: Step 1 of every inbound. Output drives every downstream branch.
inputs:
  - { name: message, type: string, required: true }
outputs:
  - { name: intent, type: string, description: "question | bug | feature | billing | other" }
  - { name: confidence, type: number, description: "0.0–1.0 self-reported confidence." }
---

# Classify Intent

## Canonical intent vocabulary

The project validator (`scripts/verify_output.py`) enforces **exactly five** intent values. Anything else fails CI.

| Canonical | What it covers | Common synonyms (map these to the canonical) |
|---|---|---|
| `question` | how-to / what-is / docs lookup | `support`, `help`, `inquiry`, `general` |
| `bug` | broken behavior, error, unexpected output | `technical`, `issue`, `incident`, `defect`, `problem` |
| `feature` | new capability requested | `feature_request`, `enhancement`, `idea`, `wish` |
| `billing` | invoices, refunds, plan changes, pricing | `payment`, `subscription`, `invoice`, `pricing` |
| `other` | anything else | `account`, `unknown`, `misc`, `legal` |

**If your task spec uses domain names like `technical` or `feature_request`, map them to the canonical set before returning.** Keep the mapping table in your code so the original term is recoverable for analytics — but the value that leaves your function must be one of the five canonical names.

## Steps

1. Read the message.
2. If it asks a how-to or what-is question → `question`.
3. If it describes broken behavior, an error, or unexpected output → `bug`.
4. If it asks for a new capability → `feature`.
5. If it's about pricing, invoices, refunds, or plan changes → `billing`.
6. Otherwise → `other`.
7. Return `confidence` honestly.

## Confidence threshold — pick deliberately

The default low-confidence threshold is **0.5** (escalate below this). **This is a tuning knob, not a constant.**

| Lower the threshold (0.3–0.4) when… | Raise the threshold (0.6–0.7) when… |
|---|---|
| Wrong answers are expensive (legal, financial, healthcare) | KB coverage is broad and answers are mostly accurate |
| Escalations are cheap (you have 24/7 staffing) | Human agents are scarce or expensive |
| Brand tolerance for "let me get someone" is high | Users complain about being bounced to humans for trivial questions |
| Early days — you're still learning the failure modes | Mature pipeline with proven recall |

**Document your chosen threshold in code with the reason.** Future-you will not remember why 0.45 won over 0.5.

## Failure modes

- Treating "this is slow" as `question` (it's a `bug`).
- Treating refund requests as `other` to dodge billing escalation rules. *Always* check trigger words (`lawyer`, `cancel`, `refund`) before the classifier — they outrank intent.
- Stacking multiple intents into one ticket — split them.
- Hard-coding the threshold without documenting the trade-off (the next maintainer can't tune it safely).
- Shipping the task-domain vocabulary (`technical`, `feature_request`) directly without mapping — breaks `harnessforge verify`.
