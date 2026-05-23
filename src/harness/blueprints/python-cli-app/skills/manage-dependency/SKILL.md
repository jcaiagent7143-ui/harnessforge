---
name: manage-dependency
description: Add, remove, or pin a Python dependency in pyproject.toml — and only when it's actually needed.
version: 1.0.0
when_to_use: Before adding any import that isn't already in the project's deps list.
inputs:
  - {name: package_name, type: string, required: true}
  - {name: justification, type: string, required: true, description: "Why this can't be done with stdlib or existing deps."}
outputs:
  - {name: pyproject_diff, type: string}
---

# Manage dependency

## Steps

1. **Check first** — is there a stdlib equivalent? Is an existing project dep already capable? If yes, **do not add a new dep**.
2. **Check the lockfile** — if there's a `uv.lock` / `poetry.lock` / `requirements.txt`, the dep manager matters.
3. **Add to `[project.dependencies]` in `pyproject.toml`** with a permissive lower bound (`yfinance>=0.2.40`). Avoid pinning the upper bound unless the project does that everywhere.
4. **Do NOT add a parallel `requirements.txt`** — one source of truth.
5. **Justify in the commit message.** "Add yfinance>=0.2.40 — Yahoo Finance price fetcher; stdlib has no equivalent and project already excluded paid alternatives."
6. **Run install** to make sure resolution works: `pip install -e .` or `uv sync`.

## Failure modes to avoid

- Adding `requests` to a project that already has `httpx`.
- Adding `pandas-ta` for `rsi(df)` when 15 lines of math do the same thing testably.
- Pinning to an exact version (`==1.2.3`) — kills upgrade paths.
- Adding a dep "in case we need it later." YAGNI.
