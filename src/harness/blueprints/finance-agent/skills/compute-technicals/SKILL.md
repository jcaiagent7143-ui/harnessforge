---
name: compute-technicals
description: Compute standard technical indicators (RSI, SMA, EMA, MACD, Bollinger) on an OHLCV frame; tested against canonical references.
version: 1.0.0
when_to_use: After fetch-market-data, before screen-positions.
inputs:
  - {name: frame, type: object, required: true, description: "pandas DataFrame with at least 'Close' column."}
  - {name: indicators, type: array, required: false, description: "Subset to compute. Default: [rsi14, sma50, sma200]."}
outputs:
  - {name: frame_with_indicators, type: object, description: "Original frame + indicator columns appended."}
---

# Compute technicals

## Canonical formulas (no hand-waving)

| Indicator | Definition |
|---|---|
| **SMA(n)** | Simple moving average of close over n bars |
| **EMA(n)** | Exponential moving average with α = 2/(n+1) |
| **RSI(14) — Wilder** | `RS = avg_gain_14 / avg_loss_14` (Wilder smoothing, not simple average); `RSI = 100 - 100/(1+RS)` |
| **MACD** | EMA(12) − EMA(26); signal = EMA(9) of MACD |
| **Bollinger(20, 2)** | SMA(20) ± 2 × stddev(20) |

The **Wilder smoothing** distinction matters — many tutorials use a simple average and get RSI values off by a few points. The first 14 bars use the simple average to seed; from bar 15 onward, each step is `(prev * 13 + new) / 14`.

## Steps

1. **Validate inputs** — frame must have `Close`. For volume-based indicators, `Volume` too.
2. **Compute in-place on a copy** — never mutate the caller's frame.
3. **Append columns** named exactly per canonical lib conventions (e.g. `RSI_14`, `SMA_50`, `SMA_200`, `MACD`, `MACD_signal`).
4. **NaN for warmup periods** — don't forward-fill the first 13 RSI values.
5. **Test against a known fixture** — at least one indicator should match a published value (e.g. RSI of a flat series = 50; RSI of monotonically increasing close → 100).

## Failure modes to avoid

- Using simple average instead of Wilder smoothing for RSI.
- Forward-filling warmup NaN — gives the screen false signals at the start of the window.
- Computing RSI on intraday bars but labeling it as daily.
- Adding pandas-ta / ta-lib as a dep for indicators you can write in 15 lines and test.
