# Python CLI App / Library blueprint

The default blueprint for *building* a Python CLI tool or library. Use
this for "write me a script", "add a command", "make a library" tasks —
not for orchestrating external systems (use `workflow-agent` for that).

## What this blueprint generates

- `AGENTS.md` — *build-mode* instructions: how to add features, what
  test runner to use, where to put new files, how to manage deps.
- `SOUL.md` — engineer-voice (not orchestration-voice). "Match the
  existing style, run the tests, ship a tight diff."
- `TOOLS.md` — recommended dev tools (uv/pip, pytest/unittest, ruff)
  and project-local commands.
- `MEMORY.md` — minimal: change log + dependency rationale.
- `SKILLS/{add-cli-command, add-unit-test, manage-dependency, check-style}/`

## When to use

- "Write me a CLI tool that does X"
- "Add a command to this library"
- "Build a small Python utility"
- "Refactor this module"

## When NOT to use

- "Build an agent that calls 5 APIs in order" → `workflow-agent`
- "Build a retrieval-augmented Q&A" → `rag-agent`
- "Build a customer-support bot" → `support-agent`
- "Build a market-data + portfolio analyzer" → `finance-agent`

## Validators

- `structure` — every blueprint-generated file is present and parses
- `tests`     — runs `profile.test_command`, exits 0
- `lint`      — runs `profile.lint_command`, exits 0
