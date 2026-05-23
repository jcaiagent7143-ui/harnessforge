# The provisioning flow

`harness init` is one command, but under the hood it's a five-stage pipeline. Each stage is independently inspectable.

## 1. Inspect

`harness.inspect_.inspect_repo(root)` walks the repo:

- Detects languages (Python, TypeScript, JavaScript, Rust, Go, Java, Ruby, PHP, Elixir)
- Detects frameworks (FastAPI, Django, Next.js, React, Vue, Svelte, Express, Hono, etc.)
- Detects package managers (pip, poetry, uv, npm, pnpm, yarn, bun, cargo, go)
- Detects CI provider (GitHub Actions, GitLab CI, CircleCI, Azure)
- Detects containerization (Dockerfile, docker-compose, kubernetes)
- Reads `.env.example` for expected env vars
- Reads README and CONTRIBUTING excerpts
- Detects existing agent configs (`AGENTS.md`, `.claude/CLAUDE.md`, `.cursor/rules`, etc.)
- Detects existing MCP configs

Pure function, no LLM, no network calls (except one short `git remote get-url`).

## 2. Profile

`harness.profile.profile_from_inspection_template(report)` or `_llm(report, provider)`:

- The template path is deterministic and works without any API key
- The LLM path refines descriptions and conventions to be project-specific
- Both produce a `HarnessProfile` dataclass
- Falls back to template on any LLM error — the build never breaks

## 3. Recommend

`harness.blueprints.recommend_blueprint(report, profile)` picks the blueprint:

- Vector-store deps or "rag"/"docs" in the name → `rag-agent`
- Django/Rails web-app or "support"/"help" in the name → `support-agent`
- Anything else → `workflow-agent` (the generic default)

Explicit `--blueprint` always overrides the recommendation.

## 4. Render

For each blueprint + chosen IDE adapter:

- Adapters write to a temp dir; outputs captured as `PlannedFile` records
- Blueprint Jinja2 templates render with `(profile, report, blueprint)` context
- Blueprint skills copy verbatim into `SKILLS/<skill-name>/`
- Everything aggregates into a `RenderPlan`

With `--dry-run`, the plan prints and nothing is written.

## 5. Write

- Each file written via tmp + atomic rename
- Manifest-aware collision policy: refuse to overwrite a user-edited file unless `--force`
- `.harness/manifest.json` records the sha256 of every file we wrote — used by `harness sync --check`

## Drift detection

`harness sync --check` reads `.harness/manifest.json` and checks every recorded file against the current on-disk hash. Any mismatch → exit 1. Drop into CI:

```yaml
- run: harness sync --check
```
