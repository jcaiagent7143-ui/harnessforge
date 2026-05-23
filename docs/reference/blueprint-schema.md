# Blueprint schema

`blueprint.yaml` is validated by `harness.blueprints.schema.BlueprintSpec`.

```yaml
name: string                  # kebab-case, required
version: string               # default "1.0.0"
display_name: string          # required
description: string           # required
agent_type: string            # required (rag | support | workflow | sales | browser | finance | other)

suitable_for:                 # optional
  project_types: [string]
  languages: [string]

recommended_mcps: [string]    # MCP server names; cross-ref harness.catalog
memory_schemas: [string]      # JSON Schemas under memory_schemas/
skills: [string]              # skill directory names under skills/

generated_files:
  - path: string              # repo-relative target
    template: string          # filename under files/
    mode: integer             # unix mode, e.g. 493 (0o755)

validators:
  - name: string
    module: string            # module name under validators/ (no .py)
    description: string

eval_set: string              # optional path under eval/

# Extra keys are preserved verbatim (extras: dict)
```

## Validator contract

Each `validators/<module>.py` must export:

```python
from pathlib import Path

def run(target: Path) -> list[str]:
    """Return failure messages. Empty list = pass.
    Strings starting with 'SKIPPED:' are not counted as failures."""
    ...
```
