# The aegis 5-stage pipeline (internal)

`aegis` was the original headline project (PyPI: `self-harness ≤ 0.5.4`). It now serves as an **internal** dependency of `harnessforge`, providing:

- **Provider abstraction** — `aegis.providers.auto_provider()` for Anthropic / OpenAI / Gemini / Ollama / LiteLLM / Mock
- **Sandbox** — `aegis.synthesize.sandbox` (AST allowlist + restricted exec + SIGALRM/RLIMIT) for running blueprint validators safely
- **Result + audit-trail types** — `StageRecord`, `AuditTrail`, `Result`

The 5-stage pipeline (analyze → assess → synthesize → execute → verify) is preserved for users who want per-task harnesses, but it's no longer the docs-promoted use case.

## When you might still use aegis directly

- You want per-task synthesized harnesses (the original Aegis use case)
- You want to call the Aegis sandbox from your own code: `from aegis.synthesize.sandbox import load_harness`
- You want to use Aegis's provider auto-detection in your own tooling: `from aegis.providers import auto_provider`

See the `src/aegis/` source for the full API. It will continue to be maintained as long as harnessforge depends on it.
