---
name: flag-attention
description: Turn screened matches into a calibrated, sourced summary the user can act on — without recommending action.
version: 1.0.0
when_to_use: Last step before reporting to the user.
inputs:
  - {name: matches, type: array, required: true, description: "Output of screen-positions."}
outputs:
  - {name: report, type: object, description: "{summary, attention_items[], generated_at, sources[]}"}
---

# Flag for attention

## Steps

1. **Group matches by ticker** — one ticker may match multiple screens.
2. **For each, write a single-sentence summary** with the numbers + threshold + source:
   - "AAPL is overbought (RSI-14 78.6 > 70) and within 0.4% of its 52-week high ($184.32 vs $185.00). Source: yfinance 2026-05-22."
3. **Sort by signal strength** — strongest divergence from threshold first.
4. **Cap the list** — if >10 matches, report the top 10 + a count of the rest.
5. **Never write "you should …"** — the user decides.
6. **Persist** to `.harness/signals_archive/<YYYY-MM-DD>.json` per `MEMORY.md`.

## Output shape

```jsonc
{
  "generated_at": "2026-05-22T16:05:00-04:00",
  "sources": ["yfinance"],
  "summary": "3 positions flagged: 2 overbought, 1 near 52w low.",
  "attention_items": [
    {
      "ticker": "AAPL",
      "screen": "overbought_rsi",
      "value": 78.6,
      "threshold": 70,
      "headline": "AAPL is overbought (RSI-14 78.6 > 70) and within 0.4% of its 52-week high ($184.32 vs $185.00). Source: yfinance 2026-05-22."
    }
  ]
}
```

## Failure modes to avoid

- Recommending action ("consider trimming AAPL"). Surface signals only.
- Headlines without numbers ("AAPL looks toppy").
- Headlines without sources / timestamps.
- Suppressing matches to "look clean" — surface them all (with the cap rule above).
