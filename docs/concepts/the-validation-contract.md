# The validation contract

`harness verify` is the single, stable interface your coding agent uses to know whether it produced a valid output.

## CLI shape

```bash
harness verify [TARGET] [--json] [--check NAME] [--fail-fast]
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | All checks passed (or all skipped — see below) |
| 1 | One or more validators reported failures |
| 2 | Configuration error (malformed `harness.config.json`, unknown blueprint) |
| 3 | No `harness.config.json` — this isn't a harness-bootstrapped repo |

## JSON contract (stable, versioned)

```json
{
  "schema_version": 1,
  "blueprint": "rag-agent",
  "blueprint_version": "1.0.0",
  "checks": [
    {
      "name": "structure",
      "description": "Every blueprint-generated file is present and parses.",
      "status": "pass",
      "duration_ms": 12,
      "messages": []
    },
    {
      "name": "citations",
      "description": "Every factual claim cites a chunk_id.",
      "status": "fail",
      "duration_ms": 45,
      "messages": ["chunk_id 'abc123' cited in text but not in citations[]"]
    }
  ],
  "summary": {
    "total": 2,
    "passed": 1,
    "failed": 1
  }
}
```

### Status values

| Status | Meaning |
|---|---|
| `pass` | Validator ran and produced zero failure messages |
| `fail` | Validator ran and produced ≥1 failure message |
| `skipped` | Validator ran but couldn't evaluate (e.g. no agent output file yet); not counted as failure |
| `error` | Validator itself raised an exception (counted as failure) |

## MCP

`harness mcp` exposes the same contract through the `harness_verify` tool. The JSON return type is identical.

## Why this matters

Your coding agent — Claude Code, Cursor, Codex, etc. — calls `harness verify --json`, reads the failure messages, and can decide:

- Retry the task with the failures as feedback
- Surface the failure to the user
- Tighten an upstream skill (e.g. add more chunks before answering)

Because the contract is stable and JSON, the agent can rely on it across versions.
