# Profile vs. blueprint

Two core abstractions sit at the heart of Harness Kit.

## Profile

A **profile** describes *your specific repo*: name, project type, primary language, frameworks, test/lint/build commands, forbidden paths, forbidden commands, conventions, success criteria, required env vars, recommended MCPs.

It's built once per `harness init` from:

1. A deterministic `inspect_repo()` walk (no LLM required), then
2. An optional LLM refinement that turns the inspection into prose-quality descriptions.

The profile is **committed to your repo** at `.harness/profile.yaml`. Future `harness sync` runs re-render adapters from it without re-inspecting.

Example:

```yaml
name: fastapi-rag-demo
description: A retrieval-augmented Q&A app over our docs.
project_type: web-app
primary_language: python
frameworks: [fastapi]
test_command: pytest
lint_command: ruff check .
forbidden_paths: [.env, .env.*, '*.pem', secrets/]
forbidden_commands: [rm -rf /, git push --force]
recommended_mcps: [filesystem, fetch, postgres, qdrant]
```

## Blueprint

A **blueprint** describes *a kind of agent*: rag, support, workflow, sales, browser, finance. It's project-agnostic — the same blueprint applies to any repo of the right shape.

Each blueprint ships:

- A `blueprint.yaml` spec
- Jinja2 templates under `files/` (AGENTS.md, SOUL.md, TOOLS.md, MEMORY.md, etc.)
- Skill bundles under `skills/` (anthropics/skills format)
- Validator modules under `validators/` (real Python, run inside the aegis sandbox)
- Memory JSON Schemas under `memory_schemas/`
- An eval question set under `eval/`

Blueprints are bundled with Harness Kit; you don't author them per-project. Authors *can* write custom blueprints — see [Authoring a custom blueprint](../guides/custom-blueprint.md).

## How they combine

`harness init` runs:

1. **Inspect** the repo (no LLM)
2. **Profile** the repo (LLM or template)
3. **Recommend** a blueprint based on the profile
4. **Render** the blueprint's templates using the profile as context
5. **Write** everything atomically into the repo

The profile feeds the templates. The blueprint shapes the agent. The two together make a complete harness.
