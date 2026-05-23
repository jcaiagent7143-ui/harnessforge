---
name: screen-positions
description: Filter the user's positions (or a universe) by declarative criteria — return only what matches.
version: 1.0.0
when_to_use: After compute-technicals, to narrow the analysis.
inputs:
  - {name: frames, type: object, required: true, description: "Output of compute-technicals."}
  - {name: criteria, type: array, required: true, description: "List of {name, predicate} screens to apply."}
outputs:
  - {name: matches, type: array, description: "[{ticker, matched_criteria[], values}]"}
---

# Screen positions

## Steps

1. **Apply each criterion as a predicate** against the latest bar of each ticker's enriched frame.
2. **Common screens** (start here):
   - `oversold_rsi`: `RSI_14 < 30`
   - `overbought_rsi`: `RSI_14 > 70`
   - `golden_cross`: `SMA_50` crosses above `SMA_200` (vs. previous bar — not just `SMA_50 > SMA_200`)
   - `death_cross`: `SMA_50` crosses below `SMA_200`
   - `near_52w_high`: latest close within 1% of trailing-252-bar max
   - `near_52w_low`: latest close within 1% of trailing-252-bar min
3. **Return a structured result** — for each matched ticker, list the criteria it matched and the values that triggered them.
4. **Don't silently coerce** — if a screen requires `RSI_14` and a ticker doesn't have enough bars, skip that ticker for that screen with a reason.

## Output shape

```jsonc
[
  {
    "ticker": "AAPL",
    "matched": ["overbought_rsi", "near_52w_high"],
    "values": {"RSI_14": 78.6, "close": 184.32, "52w_high": 185.00}
  }
]
```

## Failure modes to avoid

- "Cross" detected as `A > B` instead of "`A` was `<= B` last bar, now `>` this bar".
- 52-week extremes computed from `max(close)` instead of `max(high)`.
- Single threshold for all markets — equities `RSI_14 < 30` ≠ crypto `RSI_14 < 30` (volatility differs).
- Silent skip when a ticker lacks bars — surface it.
