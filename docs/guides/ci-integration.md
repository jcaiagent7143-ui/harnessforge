# CI integration

Two commands plug harnessforge into CI cleanly:

```yaml
- run: pip install harnessforge
- run: harness sync --check    # 1: fail if generated files drifted from manifest
- run: harness verify --json   # 2: fail if blueprint contract broken
```

## `harness sync --check`

Reads `.harness/manifest.json` and compares the sha256 of every recorded file to the on-disk version. Any drift → exit 1 with the drifted paths printed.

Use it to detect:

- Someone hand-edited a generated file (and forgot to update the profile)
- A blueprint upgrade requires re-rendering (drift will surface; run `harness sync --force`)

## `harness verify --json`

Runs the blueprint validators. Exits:

- `0` — all checks passed or skipped
- `1` — one or more failures
- `2` — config error
- `3` — repo isn't harness-bootstrapped (no `harness.config.json`)

Use it to enforce blueprint contracts in CI. Example: every PR that touches the RAG agent's output runs through the citation validator.

## Full example

```yaml
# .github/workflows/harness.yml
name: harness

on:
  push:
    branches: [main]
  pull_request:

jobs:
  harness:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install harnessforge
      - name: Check generated files are in sync with profile
        run: harness sync --check
      - name: Run blueprint validators
        run: harness verify --json
```

## What CI doesn't need

- No LLM API keys (init uses `--no-llm` semantics on CI; verify never calls an LLM)
- No vector store or DB (verify works on schemas + structure)
- No MCP setup
