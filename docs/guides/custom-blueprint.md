# Authoring a custom blueprint

Want a blueprint that ships in your fork (or upstream) for a domain not covered by `rag-agent` / `support-agent` / `workflow-agent`? Here's the contract.

## Directory layout

```
src/harness/blueprints/<name>/
  blueprint.yaml          # Pydantic-validated spec
  README.md
  files/                  # Jinja2 templates rendered into the user's repo
    AGENTS.md.j2
    SOUL.md.j2
    TOOLS.md.j2
    MEMORY.md.j2
    scripts/
      test_task.sh.j2
      verify_output.py.j2
  skills/                 # anthropics/skills bundles
    <skill-name>/
      SKILL.md
      (optional resources)
  validators/             # plain Python — each module exports run(target: Path) -> list[str]
    check_structure.py
    check_<your-thing>.py
  memory_schemas/         # JSON Schema
    conversation.json
  eval/
    questions.yaml
```

## blueprint.yaml

```yaml
name: my-blueprint           # kebab-case
version: 1.0.0
display_name: "My Blueprint"
description: "One-line summary."
agent_type: my-type          # rag | support | workflow | sales | browser | finance | other
suitable_for:
  project_types: [web-app, library]
  languages: [python, typescript]
recommended_mcps: [filesystem, fetch]
memory_schemas: [conversation]
skills: [my-first-skill, my-second-skill]
generated_files:
  - { path: AGENTS.md,            template: AGENTS.md.j2 }
  - { path: SOUL.md,              template: SOUL.md.j2 }
  - { path: TOOLS.md,             template: TOOLS.md.j2 }
  - { path: MEMORY.md,            template: MEMORY.md.j2 }
  - { path: scripts/test_task.sh, template: test_task.sh.j2, mode: 493 }
validators:
  - { name: structure,  module: check_structure,  description: "Files present + parse." }
  - { name: my_thing,   module: check_my_thing,   description: "Your invariant." }
eval_set: eval/questions.yaml
```

## Template context

Inside every Jinja2 template you have:

| Variable | What it is |
|---|---|
| `profile` | The user's `HarnessProfile` (name, description, project_type, conventions, etc.) |
| `report` | The deterministic `InspectionReport` |
| `blueprint` | This `BlueprintSpec` |
| `frameworks_list` | Pre-joined string `"fastapi, postgres"` |
| `mcps_list` | Pre-joined string of profile + blueprint MCPs |
| `skills_list` | Markdown bullet list of `blueprint.skills` |

## Validators

```python
# validators/check_my_thing.py
from pathlib import Path


def run(target: Path) -> list[str]:
    """Return a list of failure messages. Empty list = pass."""
    failures: list[str] = []
    if not (target / "REQUIRED_FILE.md").exists():
        failures.append("REQUIRED_FILE.md is missing")
    return failures
```

Conventions:

- Validators run inside the aegis AST-allowlist sandbox — no `subprocess`, no arbitrary `os.system`, no network.
- Return `["SKIPPED: reason"]` for checks that can't run yet (e.g. waiting for an agent output file). Skipped is not a failure.
- Keep failure messages human-readable and specific.

## Register

Drop the directory under `src/harness/blueprints/<name>/`. The loader autodiscovers any subdirectory containing `blueprint.yaml`. No registry edit required.

## Test

```bash
harness blueprint show my-blueprint
harness init /tmp/test-repo --blueprint my-blueprint
harness verify /tmp/test-repo --json
```

Add a golden-file test under `tests/harness/golden/test_golden_tree.py` to lock in the expected output shape.
