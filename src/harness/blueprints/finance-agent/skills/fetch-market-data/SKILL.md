---
name: fetch-market-data
description: Fetch OHLCV / quote / fundamental data from the configured source; never auto-retry on rate limits without backoff.
version: 1.0.0
when_to_use: First step of any analysis.
inputs:
  - {name: tickers, type: array, required: true}
  - {name: period, type: string, required: false, description: "e.g. 1y, 6mo, 30d. Default: 1y."}
  - {name: interval, type: string, required: false, description: "e.g. 1d, 1h. Default: 1d."}
outputs:
  - {name: frames, type: object, description: "{ticker: pandas.DataFrame} or equivalent."}
---

# Fetch market data

## Steps

1. **Validate the ticker list** — strip whitespace, uppercase, dedupe, drop empties.
2. **Choose the data source** in this preference order:
   - `yfinance` if no broker keys configured (free, anonymous)
   - `alpaca-py` if `ALPACA_KEY` + `ALPACA_SECRET` set (better data quality, included with Alpaca account)
   - `polygon-api-client` if `POLYGON_API_KEY` set (real-time)
3. **Fetch in one batch call** when the library supports it (yfinance does via `yf.download(tickers=[...])`). Don't per-ticker loop in serial.
4. **Record provenance** in session memory: `{ticker, source, fetched_at, period, interval}`.
5. **On rate-limit error**: backoff exponentially (cap 60s), retry up to 3 times; if still failing, surface the error per-ticker — don't fail the whole run.
6. **On missing ticker**: report it; don't fabricate data.

## Output shape

```python
{
  "AAPL": DataFrame(index=DatetimeIndex, columns=["Open", "High", "Low", "Close", "Volume"]),
  "MSFT": DataFrame(...),
  ...
}
```

## Failure modes to avoid

- Per-ticker serial fetch in a loop (slow + multiplies rate-limit risk).
- Silent failure on missing tickers.
- Caching forever — quote data is stale within minutes during market hours.
- Hard-coded API keys.
- Calling broker WebSocket subscriptions during a one-shot analysis (paid streaming for a single read).
