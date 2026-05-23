---
name: check-style
description: Run the project's lint + formatter before declaring done; fix what's auto-fixable.
version: 1.0.0
when_to_use: Last step of every change. Always.
inputs:
  - {name: changed_files, type: array, description: "Optional — defaults to staged + working-tree files."}
outputs:
  - {name: lint_passed, type: boolean}
---

# Check style

## Steps

1. **Run the project's linter** — `{{ profile.lint_command if profile and profile.lint_command else "ruff check . / flake8 / mypy — whatever the project declared" }}`.
2. **If the linter has an auto-fix flag** (`ruff check --fix`, `black .`), run it.
3. **Re-run** to confirm clean.
4. **Run the formatter** if separate (`ruff format .`, `black .`).
5. **If there are remaining warnings you can't auto-fix**, surface them in the summary — don't silently `# noqa` them.

## Failure modes to avoid

- Adding `# noqa` to suppress a real bug.
- Running a different formatter (`black`) when the project uses `ruff format`.
- Auto-formatting files outside your diff (touches unrelated lines, bloats the PR).
- Skipping lint with "it's just a small change."
