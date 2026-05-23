# Verify protocol

The stable JSON contract returned by `harness verify --json` and by the `harness_verify` MCP tool.

```jsonc
{
  "schema_version": 1,
  "blueprint": "rag-agent",
  "blueprint_version": "1.0.0",
  "checks": [
    {
      "name": "structure",
      "description": "Every blueprint-generated file is present and parses.",
      "status": "pass",            // pass | fail | skipped | error
      "duration_ms": 12,
      "messages": []
    },
    {
      "name": "citations",
      "description": "Every factual claim cites a chunk_id.",
      "status": "skipped",
      "duration_ms": 0,
      "messages": ["SKIPPED: no answer file found at $RAG_OUT or /tmp/*-rag-output.json"]
    }
  ],
  "summary": {
    "total": 2,
    "passed": 1,
    "failed": 0
  }
}
```

## Status semantics

| Status | Counted as failure? | Meaning |
|---|---|---|
| `pass` | No | Validator ran and produced 0 failure messages |
| `fail` | Yes | Validator ran and produced ≥1 failure message |
| `skipped` | No | Validator returned only "SKIPPED:" messages — couldn't evaluate |
| `error` | Yes | Validator raised an exception |

## Exit codes (CLI)

| Code | Meaning |
|---|---|
| 0 | `summary.failed == 0` |
| 1 | `summary.failed > 0` |
| 2 | Malformed `harness.config.json` |
| 3 | No `harness.config.json` (repo not bootstrapped) |

## Stability

`schema_version` will not change within a major version. New optional fields may appear in `checks[]` (e.g. additional metadata). Treat unknown fields as forward-compatible.
