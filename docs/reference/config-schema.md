# Config schema

`harness.config.json` is validated by `harness.config.HarnessConfig`.

```jsonc
{
  "schema_version": 1,
  "harness_version": "0.1.0",
  "blueprint": "rag-agent",
  "blueprint_version": "1.0.0",
  "manifest": ".harness/manifest.json",
  "profile":  ".harness/profile.yaml",
  "adapters": ["claude-code", "cursor", "continue", "codex-cli", "windsurf"],
  "skills_dir": "SKILLS",
  "extras": {}
}
```

| Field | Type | Description |
|---|---|---|
| `schema_version` | int | Always 1 in v0.1. Bumped on breaking changes. |
| `harness_version` | string | Version of harness-kit that wrote this file. |
| `blueprint` | string | Blueprint name (`rag-agent`, etc.). |
| `blueprint_version` | string | Blueprint version. |
| `manifest` | string | Path to the file manifest (default `.harness/manifest.json`). |
| `profile` | string | Path to the canonical profile (default `.harness/profile.yaml`). |
| `adapters` | array of strings | IDE adapters rendered (`claude-code`, `cursor`, `continue`, `codex-cli`, `windsurf`). |
| `skills_dir` | string | Where SKILLS live (default `SKILLS`). |
| `extras` | object | Forward-compatible bag. Unknown keys are preserved on read. |
