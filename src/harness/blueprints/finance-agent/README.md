# Finance / Market Data Agent blueprint

Build a market-data + portfolio-analysis agent. **Read-only by default.**
Placing orders or moving money requires an explicit human-approval gate
that the `no_trades_without_gate` validator enforces.

## When to use

- Personal portfolio analyzer (stocks, crypto, ETFs)
- Market screener / signal generator
- Backtest harness
- Equity research notebook

## When NOT to use

- A trading bot that auto-executes — that crosses into "moves money" territory and needs serious safety review beyond what this blueprint provides
- A general data pipeline (use `workflow-agent`)
- A retrieval Q&A over filings/research (use `rag-agent`)

## What gets generated

- `AGENTS.md` — analyst voice + the read-only-by-default rule
- `SOUL.md` — "calibrated, hedged-when-uncertain, never a recommendation without evidence"
- `TOOLS.md` — yfinance / Alpaca / Polygon / ccxt recommendations
- `MEMORY.md` — positions schema + signals schema
- `SKILLS/{fetch-market-data, compute-technicals, screen-positions, flag-attention}/`

## Validators

- `structure` — every blueprint file present
- `tests` — project test_command exits 0
- `no_trades_without_gate` — scans the repo for `order(`, `buy(`, `sell(`, `place_order(`, `submit_order(` not preceded by an approval check
