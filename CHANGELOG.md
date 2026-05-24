# Changelog

All notable changes to harnessforge (PyPI: `harnessforge`) and the legacy
distribution (`self-harness`) are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [harnessforge 0.2.2] — 2026-05-24 — patch: 3 friction issues caught by the post-PyPI support-agent eval

First public-release eval (real Claude Code subagent on a never-tested
blueprint — `support-agent`) confirmed the headline thesis: the
harness-equipped agent shipped **45 tests vs. 34** in **15 min vs. 20 min**
on **420 LoC vs. 572 LoC**, and caught a real defect the control would have
committed (task spec used `technical`/`feature_request`/`account` intent
names; project validator enforces `bug`/`feature`/`other` — the harness
agent read the validator, mapped, and shipped; the control didn't know
the validator existed). Full eval artifacts in `/tmp/eval-control` and
`/tmp/eval-harness` at eval time.

The eval surfaced three small friction issues; v0.2.2 patches every one.

### Fixed

- **pytest-install friction across all 5 blueprints**. The harness eval
  agent spent ~3 of 15 min locating a Python interpreter with pytest
  because the generated AGENTS.md never mentioned pytest as a test
  dependency. All 5 blueprints' `AGENTS.md.j2` now ship a `## Setup`
  section: *"First-time test run: this project uses pytest. If `pytest:
  command not found`, run `pip install pytest`. That's the only setup
  step."* Eliminates 20% of the friction the eval observed.

- **support-agent intent-vocabulary discoverability**. The validator's
  canonical intent set (`question / bug / feature / billing / other`)
  rarely matches a task brief's natural vocabulary (`technical /
  feature_request / account`). v0.2.1's `classify-intent` SKILL.md only
  listed the canonical set; agents had to read `scripts/verify_output.py`
  separately to discover the constraint. SKILL.md now ships an explicit
  mapping table with the canonical set in column 1 and common synonyms
  (`technical → bug`, `feature_request → feature`, `account → other`,
  ...) in column 3. Bumped SKILL `version: 1.0.0 → 1.1.0`.

- **classify-intent confidence threshold documented as a tuning knob,
  not a constant**. SKILL.md previously read "below 0.5 → escalate" as
  a hard rule; the eval agent felt compelled to deviate to 0.45 and
  document why. SKILL.md now ships a trade-off table: *lower (0.3–0.4)
  when wrong answers are expensive (legal/financial/healthcare); raise
  (0.6–0.7) when KB coverage is high and human bandwidth is scarce*.
  Guides instead of dictates.

### Added

- **`tests/harness/unit/test_v022_eval_patches.py`** — 8 regression
  tests guarding the three fixes against silent regression. The eval
  found these gaps because they were undocumented invariants; the tests
  make them invariants.

### Methodology note

The v0.2.2 eval design (parallel Claude Code subagents, blueprint not
previously A/B'd, real PyPI install path, identical task prompt with no
mention of harnessforge to either agent) is now the standard release-gate
pattern. v0.3 will run the same pattern against `rag-agent` (last blueprint
not yet eval'd).

## [harnessforge 0.2.1] — 2026-05-23 — patch: 5 polish issues caught by the v0.2 re-eval

A second real-build A/B (Claude Code rebuilding the same stock-agent
against v0.2's `finance-agent` blueprint) confirmed the v0.2 thesis —
three of the SKILL files prevented real bugs that v0.1 missed
("Wilder smoothing", cross detection, 52w extremes). The same eval
surfaced 5 polish-level gaps; v0.2.1 patches every one.

### Fixed

1. **`python` vs `python3` on macOS** — `_pick_test_command` now
   probes PATH and embeds whichever binary actually exists. v0.2
   hardcoded `python -m unittest discover`; on stock macOS (which
   only ships `python3`) `harness verify --tests` failed on first run.
2. **Memory schemas referenced but never written** — blueprint-bundled
   `memory_schemas/*.json` are now copied into the user's
   `.harness/memory_schemas/`. v0.2's `MEMORY.md` pointed at
   `.harness/memory_schemas/positions.json` and `signals.json` but
   never copied the files; the path references were dead.
3. **Blueprint-level MCP pruning** — `_merge_and_prune_mcps` now
   applies the same evidence rules to `blueprint.recommended_mcps`
   that we apply to `profile.recommended_mcps`. `finance-agent`
   declares `postgres`; v0.2 rendered it into AGENTS.md even for a
   single-file portfolio CLI with no DB deps. Now pruned.
4. **MCP dedup** — all 10 blueprint templates (5 × `AGENTS.md.j2`
   + 5 × `TOOLS.md.j2`) now iterate `pruned_mcps` (a set-based
   merge) instead of `profile.recommended_mcps + blueprint.recommended_mcps`.
   v0.2 listed `filesystem` twice in finance-agent output.
5. **Forbidden-commands pruning** — `_default_forbidden_commands` now
   takes the `InspectionReport`: only includes `kubectl --context=prod*`
   when `has_kubernetes`, `terraform apply` when `.tf` files present,
   `DROP DATABASE`/`TRUNCATE` when DB deps detected. Universal
   destructives (`rm -rf`, `git push --force`) always included.
   v0.2 had all 4 stack-specific commands in every project regardless
   of evidence; the eval flagged this as "template bloat that dilutes
   the parts that matter".

### Added

- New `harness.blueprints.render_blueprint_memory_schemas(bp, root)`
  function. Exported from `harness.blueprints`.
- New `harness.profile._resolve_python_binary()` helper.
- New `harness.blueprints.loader._merge_and_prune_mcps(profile, bp, report)`
  helper exposed for testing.
- Template variable `pruned_mcps` (list[str]) now available in every
  blueprint template; legacy `mcps_list` (str) also updated to use
  the pruned set.
- 12 new regression tests in `tests/harness/unit/test_v021_patch.py`,
  one per issue and one per evidence-driven inclusion rule.

### Tests

- **186 tests passing** (174 in v0.2 → +12 v0.2.1 regression tests).
- All 7 golden-file snapshots updated for the new memory_schemas paths.

## [harnessforge 0.2.0] — 2026-05-23 — closes every gap from the real-build eval

A real-developer A/B build (Claude Code building a stock-analysis agent
WITH harness vs. on a bare repo) surfaced 7 specific gaps in v0.1. v0.2
closes every one.

### Added

- **`python-cli-app` blueprint** — the 80% case the v0.1 eval flagged.
  For "build me a CLI / library / web API" tasks where the deliverable
  is *code*, not an orchestration trace. Ships skills: `add-cli-command`,
  `add-unit-test`, `manage-dependency`, `check-style`. Build-mode SOUL.
- **`finance-agent` blueprint** — market data + portfolio analysis.
  Read-only by default; placing orders requires an explicit per-action
  human-approval gate enforced by the new `no_trades_without_gate`
  validator. Ships skills: `fetch-market-data`, `compute-technicals`,
  `screen-positions`, `flag-attention`. Memory schemas for `positions`
  and `signals`.
- **`harness skills add --domain <name> --description "..."`** —
  scaffold a project-specific skill under `SKILLS/domain/<name>/`. The
  blueprint catalog stays clean; project-specific procedures
  (`fetch-prices`, `compute-pnl`, etc.) live in `domain/`.
- **`harness verify --tests` and `harness verify --lint`** — shorthand
  flags that route to the corresponding validators. Plus a clear error
  message when a check name isn't defined for the chosen blueprint.
- **New validators that run real project commands** — `check_tests` and
  `check_lint` read `.harness/profile.yaml` and invoke the project's
  declared `test_command` / `lint_command`. The "definition of done:
  `harness verify` exits 0" promise is no longer a tautology.

### Changed (surgical fixes from the eval)

- **Test-runner smart default** (Fix 6) — `profile.test_command` is no
  longer `null` for Python projects without an explicit runner. Defaults
  to `python -m unittest discover` (stdlib, always works). Eliminates
  the "guess pytest vs unittest" failure mode both agents in the A/B
  eval ran into.
- **MCP-list pruning** (Fix 3) — `_default_mcps_for` now requires
  evidence: postgres only if `psycopg`/`sqlalchemy` deps detected;
  `fetch` only if HTTP-client deps OR a web framework; `kubernetes`
  only if `has_kubernetes`. A portfolio CLI no longer gets `postgres`
  recommended, which the eval flagged as eroding agent trust.
- **Forbidden-paths pruning** (Fix 3) — `migrations/`, `.aws/credentials`,
  `.ssh/`, and `.next/`/`node_modules/` now only included when there's
  evidence they apply (the directory exists, or the relevant framework
  is present, or `aws`/`ssh` appears in the README). Universal sensitive
  globs (`.env`, `*.pem`, `secrets/`) remain always-included.
- **Approval-list pruning** (Fix 3) — `requires_human_approval` no
  longer mentions `migrations/` when no `migrations/` dir exists; adds
  `.env` rule only when `.env`/`.env.example` is present; adds k8s rule
  only when `has_kubernetes`.
- **Inspector dep-family detection** — `_detect_python` now tags 30+
  more deps as `frameworks`/`notes` entries:
  - **RAG**: langchain, llama-index, qdrant-client, chromadb, pinecone-client, weaviate-client, faiss-{cpu,gpu}
  - **Finance**: yfinance, alpaca-py, ib_insync, polygon-api-client, ccxt, alpha_vantage, finnhub-python, pandas-ta
  - **Workflow**: apache-airflow, prefect, dagster, celery, luigi
  - **HTTP client**: httpx, requests, aiohttp
  - **DB**: psycopg, psycopg2, sqlalchemy, asyncpg
- **Recommender now routes 5 blueprints** (Fixes 1+2+5) — finance-agent
  for stock/portfolio/yfinance/alpaca signals; rag-agent for
  langchain/qdrant signals; support-agent for django+web-app+support
  signals; workflow-agent for airflow/prefect/ETL signals;
  python-cli-app as the new build-mode default for Python projects
  (web-app/web-api/cli/library/other) without explicit orchestration
  signals.
- **`harness skills` recurses into `SKILLS/domain/`** so user-authored
  domain skills surface alongside blueprint-shipped skills.

### Tests

- **174 tests** (up from 129 in v0.1), all passing.
- New: `test_v02_smart_defaults.py` (16 tests covering each gap surgically).
- New: `test_v02_domain_skills.py` (3 tests for the `SKILLS/domain/` convention).
- Existing parametrized suites extended to all 5 blueprints.
- Fixed: `test_validator_skipped_marker_not_counted_as_failure` now
  uses `monkeypatch.setenv("RAG_OUT", …)` to isolate from stray
  `/tmp/*-rag-output.json` files between test runs (caught during the
  real-agent eval).

### Internal

- `harness.inspect_.report._detect_python` is now the single source of
  truth for dep-family tagging — both the recommender and the MCP
  pruner read from `report.frameworks` + `report.notes`.

## [harnessforge 0.1.0] — 2026-05-23 — first public release

**Project rename + new headline product.** What used to be `self-harness`
(Aegis, the per-task synthesizing pipeline) is now `harnessforge` (the
universal harness layer for AI coding agents). `aegis` remains importable
as an internal module — the sandbox + provider abstraction + cache layer
that `harness verify` uses.

### Added

- **`harness` CLI** — `init`, `sync`, `inspect`, `verify`, `doctor`, `mcp`,
  `blueprint {list,show,apply}`, `skills {list,show,add}`, `version`.
- **Provisioning orchestrator** (`harness.provision`) — atomic writes,
  manifest-aware collision policy, dry-run support, adapter filtering.
- **Five IDE adapters** rendered from a single `HarnessProfile`:
  - `.claude/CLAUDE.md`
  - `.cursor/rules`
  - `AGENTS.md` (OpenAI Codex CLI convention)
  - `.continue/config.json`
  - `.windsurf/rules` (new — fixes the pre-existing broken import)
- **Universal harness file set** rendered per blueprint:
  - `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md` — convergent file convention shared with Hermes, OpenClaw, OpenHarness
  - `SKILLS/<name>/SKILL.md` — [`anthropics/skills`](https://github.com/anthropics/skills)-compatible
- **Three production-grade blueprints**:
  - `rag-agent` — citation-enforced Q&A with recall/precision eval
  - `support-agent` — intent → KB → ticket → escalate with SLA lineage
  - `workflow-agent` — Zapier-style orchestration with tool-log + idempotency validators
- **Anthropic-skills I/O** (`harness.skills_io`) — parse, write, list, validate
  `SKILL.md` files with YAML frontmatter.
- **Curated MCP catalog** (`harness.catalog`) — 25 OSS servers across `rag`,
  `support`, `workflow`, `infra`, `browser` agent types.
- **Memory schemas** — `conversation`, `rag-chunks`, `ticket-history` as
  JSON Schema.
- **Validator runtime** (`harness.validators`) — loads blueprint-defined
  Python modules through the aegis sandbox; returns stable JSON contract.
- **Drift detection** (`harness.manifest`) — `harness sync --check` exits
  non-zero in CI when generated files have been hand-edited.
- **MCP server** (`harness mcp`) — five typed tools:
  `harness_inspect`, `harness_blueprint_list`, `harness_skills_list`,
  `harness_verify`, `harness_profile_read`.
- **129 tests** across unit, golden-file, interop, and integration tiers.
  **83% line coverage** on `src/harness/`.
- **Three hero demos** under `examples/hero/`: FastAPI full-stack template
  × `rag-agent`, Zulip × `support-agent`, Apache Airflow × `workflow-agent`.
- **mkdocs-material docs site** at `docs/` covering concepts (incl. the
  five harness layers + vs. Hermes/OpenClaw/OpenHarness), guides,
  blueprint reference, cookbook, and CLI reference.

### Changed

- PyPI distribution renamed: `self-harness` → `harnessforge`.
- Primary console script: `harness` (was `aegis`).
- `aegis` console script kept for back-compat; marked legacy in `--help`.
- Both `src/harness/` and `src/aegis/` ship in the same wheel.
- README rewritten to reflect the new product identity, with a side-by-side
  comparison vs. Hermes, OpenClaw, OpenHarness, Mastra, OpenAI Agents SDK.

### Internal

- `aegis.providers.auto_provider`, `aegis.synthesize.sandbox`, and
  `aegis.core.result.*` are now the internal LLM I/O + sandbox + telemetry
  layer that `harness verify` and `harness.profile_from_inspection_llm`
  use under the hood.

## [self-harness 0.5.4] — 2026-05-23

Two real bugs caught by a fresh-venv end-to-end test of v0.5.3 from PyPI.
Both led to silently-broken runs that returned `value: null` or `[mock] ...`
text without the caller knowing why. Both fixed and covered by regression
tests.

### Fixed (2 real bugs)

1. **Cache poisoning across providers and across success boundaries.**
   The v0.5.2/0.5.3 pipeline wrote every synthesized harness to the cache
   *before* the run actually executed (`pipeline.py:124-125`) and looked
   it up *regardless* of which provider was active. So:

   - A run that hit the Mock provider (e.g. `OPENAI_API_KEY` set but
     `[openai]` extra missing → silent Mock fallback) stored its fallback
     template harness in the cache.
   - A subsequent run with a real provider for the *same goal text*
     short-circuited to the cached fallback harness — never calling the
     real LLM, returning `value: null`, `tokens: 0`, `duration: 1ms`.

   The fix is two-part:
   - **Defer cache writes** until after `_run_with_harness` returns with
     `result.audit.succeeded == True`.
   - **Skip cache reads and writes** when the active provider is the
     auto-fallback Mock (tagged `_is_auto_fallback=True` by
     `auto_provider()`). Explicit `provider=Mock(...)` used in unit tests
     is still allowed to cache normally.

   Regression test: `tests/unit/test_pipeline_e2e_mock.py::test_failed_run_does_not_poison_cache`
   and `::test_auto_fallback_mock_skips_cache`.

2. **`auto_provider()` silently chose OpenAI without the `openai`
   package installed.** Because `from aegis.providers.openai import
   OpenAI` imports the *adapter class* (not the openai SDK), the
   `try/except ImportError` in `auto_provider()` never tripped, even
   when `pip install self-harness` was used without the `[openai]`
   extra. The user would set `OPENAI_API_KEY`, run `aegis run …`, and
   then crash 4 stages deep with `ModuleNotFoundError: No module named
   'openai'` traced through analyze → provider.complete → _get_client.

   Fix: `OpenAI.__init__` now eagerly tries `import openai` and raises a
   clear `ImportError("OpenAI provider requires the `openai` package.
   Install with: pip install \"self-harness[openai]\"")` at
   construction time. `auto_provider()` catches it and either picks the
   next provider or, on the Mock-fallback path, prints a loud stderr
   warning naming the missing extra. Same treatment applied to
   Anthropic, Gemini, and Ollama paths.

### Changed

- `OpenAI(model=...)` now defaults to `os.environ.get("AEGIS_MODEL")`
  before the hardcoded `"gpt-4o-mini"`. So `AEGIS_MODEL=gpt-5.4-nano…`
  in the user's env / MCP config now actually selects that model
  without needing to pass it explicitly. Anthropic and Gemini already
  honored AEGIS_MODEL — OpenAI was the inconsistent one.

### Internal

- Pipeline gained `_provider_is_mock()` helper that distinguishes the
  auto-fallback Mock (tagged by `auto_provider`) from an explicit
  `Mock()` passed by a test. Only the former disables caching.
- Test count: 87 passing (was 85).

## [0.5.3] — 2026-05-23

CI cleanups + install-path cleanups. The package is now live on PyPI
(`pip install self-harness`), so every doc that still pointed at the
`git+https://github.com/jcaiagent7143-ui/harnessforge.git` install path has
been updated. All MCP config examples now use `uvx --from "self-harness[mcp,openai]" aegis mcp`
so non-Python users don't need to manage a venv at all.

### Fixed

1. **mypy --strict clean across the whole `src/aegis` tree.** The v0.5.2
   CI lint job failed with 18 errors after the new mypy override config
   exposed previously-hidden issues. Now zero errors on `mypy src/aegis`.
   The interesting one: `HarnessCache.list()` was shadowing `builtins.list`
   inside the class scope and mypy was using *the method* in the return
   annotation `list[CachedHarness]` of every other method, silently
   producing nonsense types. Method renamed to `list_all()` (callers in
   `cli/__main__.py`, tests, and CHANGELOG history updated). Plus return
   annotations added to `OpenAIProvider.stream`, `proxy._stream_text`,
   `_build_server`, `_render_result`, `_summarize`, and the verifier now
   asserts `list[str]` shape before returning to remove an `Any` leak.

2. **`lint` workflow now installs the optional extras.** Previously only
   `[dev]` was installed, so mypy couldn't resolve `fastapi`, `mcp`,
   `openai`, `textual` imports and we papered over it with `ignore_missing_imports`
   for everything. Now installs `[dev,proxy,mcp,openai]` and the
   ignore-missing-imports list shrinks to only the providers we genuinely
   don't ship by default (gemini, ollama, litellm, vcr).

3. **`web/app.py` `_tool_runtime` no-None safety.** The websocket handler
   built a `tool_callable` from `aegis.tools.get(name)` which can return
   `None` — mypy caught this and so could a user with a misconfigured
   tool registry. Now raises `KeyError` with the tool name instead of
   `AttributeError: NoneType has no attribute 'fn'` deep in the harness.

### Changed

- **All install paths switched from git+https to PyPI.** README,
  `docs/guides/use-with-your-ai-coding-tool.md`, and the CLI docstring
  for `aegis mcp` now show:

      pip install self-harness                       # core
      pip install "self-harness[mcp,openai]"         # MCP + OpenAI
      uvx --from "self-harness[mcp,openai]" aegis mcp   # zero-install MCP

  The seven MCP config examples (Claude Code, Cursor, Cline, Continue.dev,
  Windsurf, Gemini, fallback) were updated to use the `uvx --from` form
  so the user's MCP client spawns a fresh ephemeral venv per launch — no
  `pip install` step required before editing the JSON.

### Internal

- `pyproject.toml` mypy overrides: added `aegis.mcp.server` (untyped
  decorators from the mcp SDK) and `benchmarks.*` (research code, relaxed
  `disallow_untyped_defs`). Added `textual.*`, `mcp.*`, `fastapi.*`,
  `uvicorn.*` to the `ignore_missing_imports` list so the lint job stays
  green even if those optional extras aren't installed in some CI matrix.
- `ruff per-file-ignores`: `scripts/**` and `docs/**` get `RUF001/002/003`
  exemption (Unicode box-drawing characters in CLI scripts and docs are
  intentional).

## [0.5.2] — 2026-05-23

The two CI failures from v0.5.1 (the previous push). Same content goal as
this release, just split across two tags because CI was the test surface.

- `test` workflow: install `[dev,proxy,mcp,openai]` extras so the MCP
  and proxy test paths actually have their dependencies.
- `lint` workflow: ruff per-file-ignores for `src/aegis/cli/**`
  (`typer.Option(...)` is the documented API) and `src/aegis/core/risk.py`
  (StrEnum inheritance pattern is intentional).

## [0.5.1] — 2026-05-23

Bug-fix release driven by a real end-to-end MCP test against gpt-5.4-nano.
Four real issues surfaced — three doc fixes and one structural API change to
make MCP failures actionable.

### Fixed (4 real bugs)

1. **MCP env-var propagation gotcha — now loud everywhere.** MCP subprocesses
   do NOT inherit the parent shell's environment variables. If a developer
   configured `aegis mcp` in their AI tool with an empty `"env": {}` block
   while having `OPENAI_API_KEY` only in `~/.zshrc`, Aegis silently fell
   through to the Mock provider and returned `"[mock] ..."` placeholder
   output. Every MCP config example in the docs (README + use-with-AI-tool
   guide) now has a 🚨 callout explaining this is required and what happens
   if you miss it. Added an explicit troubleshooting entry: "Aegis returns
   `[mock] …` even though I set my API key".

2. **`web_search` built-in tool limitations now documented at the source.**
   DuckDuckGo's HTML endpoint rate-limits aggressively and returns sparse
   results for time-sensitive queries — the most common cause of
   `succeeded=false` on research-style goals in the external test against
   "Find top 5 startups in YC W26". The `web_search` docstring now spells
   out the limitation and links to working Tavily / Brave Search override
   examples in `docs/guides/adding-tools.md`. The guide now has full
   copy-paste snippets for Tavily, Brave, Perplexity, Exa.

3. **`aegis_run` MCP response now includes `failure_diagnostics` when
   `succeeded=false`.** Previously, a refusal returned
   `{succeeded: false, value: null, tool_calls: []}` with no signal as to
   why. Now we surface the last verify failures, the last execute-stage
   notes, and a `summary` field. Importantly, when the run "succeeded" but
   the provider was Mock and the value starts with `[mock]`, we add a
   `likely_cause` hint pointing at the env-not-propagated bug — so the
   caller can diagnose without reading the audit JSON.

4. **End-to-end MCP integration test committed.** New module
   `tests/integration/test_mcp_e2e.py` spawns the real `aegis mcp`
   subprocess and drives it via the official MCP client SDK — the same way
   Claude Code / Cursor / Cline do. Covers: initialize, list_tools,
   aegis_list_risks, aegis_assess, aegis_run + aegis_inspect round-trip,
   Mock-fallback detection, unknown-tool error path, missing-arg error
   path. Skipped automatically if the `aegis` CLI isn't on PATH or the
   `mcp` Python package isn't installed.

### Notes from the external test
- `provider: "openai"` real run on gpt-5.4-nano-2026-03-17 took 112s and
  used 5,713 tokens for the YC W26 goal. The LLM-synthesized harness was
  high-quality (7 risks identified with rich rationale, custom
  `SYSTEM_PROMPT`, Pydantic `HttpUrl` validation, custom `repair_feedback`).
- The pipeline correctly refused (`succeeded: false`) because DuckDuckGo
  returned no usable results — exactly the behavior Aegis is supposed to
  produce vs. a raw LLM call that would have hallucinated 5 plausible
  fake startup names.

### Tests
- 78/78 unit tests still passing.
- New `tests/integration/test_mcp_e2e.py` — 7 tests, all passing locally
  against the Mock provider; auto-skips in environments without the CLI
  or MCP SDK.

---

## [0.5.0] — 2026-05-23

The "your own LLM does the work" release. Aegis becomes primarily a **skill**
your LLM applies itself in-conversation, not a subprocess that spins up
another LLM. This is the architectural pivot users have been asking for
since v0.1: when you're using Claude, *Claude* should do the 5-stage
methodology — not Claude calling out to some other model that runs in the
background while Claude waits for a response.

### Added — primary "skill" form (no second LLM, no API key, no subprocess)
- **SKILL.md is completely rewritten** as a self-applied methodology rather
  than a delegation skill. The whole methodology — the 5-stage procedure,
  the full 30-entry risk catalog, the harness template, the worked example,
  the verification checklist — is now inline in the markdown so Claude can
  apply it without calling out anywhere.
- When a Claude user imports this repo as a skill (Claude Code / Chat /
  Cowork), Claude reads SKILL.md once, then for each risky task does all 5
  stages itself in the same conversation using its own model and its own
  tools (Bash, Edit, Read, WebFetch, etc.). The user sees every stage
  inline. No API key for Aegis itself is needed; no second model is called;
  there is no subprocess.
- Trade-off documented honestly: Claude reasons ~3-5× longer per task to
  produce the audit trail and refusal. Same LLM means same blind spots, so
  the verifier catches structural issues (schema, citation existence,
  arithmetic recomputation, …) — not subtle reasoning errors only a
  different model would catch.

### Changed
- **README restructured** around the "two forms, when to use which" table.
  The skill form is the recommended path for Claude users; the Python
  runtime + MCP server + HTTP proxy remain the secondary path for non-skill-
  aware tools (Codex CLI, Aider, Open WebUI, generic OpenAI clients) where
  the host LLM can't follow the methodology on its own.
- The Python runtime, MCP server, and HTTP proxy are unchanged from v0.4.2
  — they're still the right answer for tools that can't load a skill.

### Notes on the architectural choice
- For Claude users: one model, one bill, one audit trail. No "Claude calls
  GPT in the background" weirdness.
- For non-Claude users (Codex, Aider, etc.): the runtime delegates because
  Codex doesn't have a way to read + apply a skill at conversation time.
  Documented clearly in the "Which form do I use?" table.

### Tests
- 78/78 unit tests still passing (no code changes; pure docs/skill rewrite).
- The skill itself can be eyeball-tested by importing the repo into Claude
  Code and asking it to apply Aegis to a real task.

---

## [0.4.2] — 2026-05-23

Triggered by an external review that mis-identified `pypi.org/project/aegis-harness/`
(Alejandro Piad's TUI orchestrator) as our codebase — and was right to. Our
v0.4.0/v0.4.1 SKILL.md/README directed users to that name, so the confusion
was structurally our fault. This release closes the loop on two fronts:

### Added
- **Anti-confusion banner** at the top of README + SKILL.md naming the
  collision explicitly (`apiad/aegis` is a different project) and pointing
  at the correct git-based install command.
- **Git-based install commands everywhere** as the recommended path until
  `self-harness` is published on PyPI. Each occurrence shows both the
  current (git+https) and post-publish (`pip install self-harness`) form so
  the docs survive the publication moment without further edits.
- **OpenAI Codex CLI** + **Gemini CLI** entries in the integration table
  and dedicated sections in `docs/guides/use-with-your-ai-coding-tool.md`
  showing the exact env-var + base-URL setup for each. Codex uses the
  proxy; Gemini CLI gets both proxy and direct-MCP recipes.
- **Incremental audit-trail persistence** (`Pipeline(audit_path=...)`).
  The 5-stage pipeline now writes the audit JSON to disk after every
  stage via an atomic ``.partial → rename`` write, so a process crash or
  kill mid-pipeline leaves a recoverable trail showing exactly which
  stages completed. `Aegis.run()` enables this by default, pointing at
  `cache_dir/runs/_in_flight.json` during execution and finalizing to
  `cache_dir/runs/<run_id>.json` on completion. Closes criticism #7 of
  the external review.
- New test module `tests/unit/test_incremental_persistence.py` (3 tests):
  happy path stage-by-stage, mid-pipeline crash recovery, persistence
  failure must not break the pipeline.

### Changed
- MCP-config examples for Claude Code etc. use `"command": "aegis"` rather
  than `"command": "uvx"` while we're on the git-install path — uvx requires
  PyPI to fetch from. Switch back to uvx once publication is live.
- README badge bumped to 0.4.2.

### Notes for the external reviewer
- Items #1–#6 and #8 of the v0.4.0 review described `pypi.org/project/aegis-harness/`
  (apiad/aegis), not this project. Different author, different repo,
  different architecture. Worth re-running the review against the actual
  codebase via the git-install command above.
- Item #7 (state durability) is fixed in this release.
- Item #9 (skill/docs/package mismatch) was the root cause of the entire
  confusion and is closed by the rename + git-install messaging + banner.

### Tests
- **78 unit tests** (was 75), all passing.

---

## [0.4.1] — 2026-05-22

Bug-fix release surfaced by an external-developer test of the v0.4.0 GitHub
release. Two real issues caught and fixed; functionality unchanged.

### Breaking
- **PyPI distribution renamed `aegis-harness` → `self-harness`.** The old name
  was already owned by an unrelated project on PyPI (Alejandro Piad's TUI
  meta-harness — different project, coincidentally also at v0.4.0).
  Publishing under `aegis-harness` would have failed with a name conflict;
  users following the v0.4.0 README would have installed someone else's
  package. The Python import path is unchanged:

      pip install self-harness                # was: pip install aegis-harness
      from aegis import Aegis                 # unchanged

  Every doc, install command, MCP config example, and provider error
  message has been updated.

### Fixed
- **Rich tag parser was eating `[proxy]` / `[mcp]` / `[web]` in error
  messages.** Running `aegis proxy` without the proxy extras installed
  printed `Install proxy extras: pip install 'aegis-harness'` — the
  `[proxy]` portion was silently stripped because Rich treats brackets
  as style tags. All three "install the extras" hints now escape the
  brackets so users see the correct command.
- User-Agent header in `web_search` and `fetch_url` tools updated from the
  placeholder `github.com/aegis-harness` to the real repo URL.
- A LAUNCH.md filesystem path was accidentally rewritten during an earlier
  global username find-replace; restored.

### Migration notes for v0.4.0 users
If you installed via `pip install aegis-harness` against v0.4.0 docs:

    pip uninstall aegis-harness
    pip install self-harness          # or for everything: pip install 'self-harness[all]'

GitHub repo URL is unchanged: <https://github.com/jcaiagent7143-ui/harnessforge>

---

## [0.4.0] — 2026-05-22

The "any AI tool can use Aegis" release. Two new distribution surfaces mean
developers using Claude Code, Cursor, Cline, Continue, Windsurf, Aider, or
anything OpenAI-compatible can plug Aegis in without writing Python.

### Added — MCP server
- `aegis mcp` — Aegis as a Model Context Protocol stdio server. Any
  MCP-compatible AI assistant can spawn it and call its four tools:
  `aegis_run`, `aegis_assess`, `aegis_inspect`, `aegis_list_risks`.
- New module `aegis.mcp` (entry point `aegis.mcp.server.run`).
- Install: `pip install 'self-harness[mcp]'` or `uvx self-harness mcp`.

### Added — OpenAI-compatible HTTP proxy
- `aegis proxy --port 8000` — exposes `/v1/chat/completions`, `/v1/models`,
  `/health`. Aegis runs every request through the 5-stage pipeline by default
  and returns the OpenAI response shape with an extra `aegis` field carrying
  the audit metadata.
- Per-request mode override via `X-Aegis-Mode: aegis|passthrough` header.
- Streaming (SSE) supported.
- New module `aegis.proxy`. Install: `pip install 'self-harness[proxy]'`.

### Added — guide
- `docs/guides/use-with-your-ai-coding-tool.md` — copy-paste configs for
  Claude Code, Cursor, Cline, Continue, Windsurf (MCP) and Aider, Open WebUI,
  GPT-Pilot (proxy).

### Fixed
- **Sandbox limits in background threads.** `run_with_limits` previously
  crashed when called from a non-main thread (FastAPI/uvicorn workers,
  asyncio thread pools, celery) because `signal.signal()` only works in the
  main thread. Now falls back to no enforcement with a stderr warning,
  matching the Windows behavior. The proxy and any other multi-threaded
  caller now works without surprise.

### Tests
- **75 unit tests** (was 58). New modules:
  - `test_mcp_server.py` — handler unit tests + tool-registration shape.
  - `test_proxy_app.py` — FastAPI TestClient tests covering basic completion,
    multimodal content, mode-header override, streaming, error paths.

---

## [0.3.0] — 2026-05-22

The "fully dynamic harness" release. The LLM now writes the *entire* agent runtime
per task — not just safety code.

### Breaking
- `Pipeline(max_repairs=...)` default changed from `1` to `None`. `None` means
  "use whatever the synthesized harness declared as `MAX_REPAIRS`." Pass an int
  to force a global ceiling.
- `Aegis(max_repairs=...)` default likewise `None`. Existing callers that explicitly
  passed an int keep their behavior; callers relying on the implicit `1` will now
  see the harness's value used instead (usually 1 or 2 — varies per task).

### Added — the v0.3 harness contract
The synthesized harness module may now define (in addition to the required
`Output` / `ALLOWED_TOOLS` / `verify`):

- `SYSTEM_PROMPT: str` — the system message for the execute stage, written
  per-task by the LLM. Default falls back to a generic message.
- `MAX_STEPS: int` — loop budget (1..50, default 8).
- `MAX_REPAIRS: int` — post-verify retry budget (0..5, default 1).
- `MAX_TOKENS_PER_TURN: int` — per-turn token budget (64..16384, default 2048).
- `TEMPERATURE: float` — sampling temperature (0.0..2.0, default 0.0).
- `TOOL_OVERRIDES: dict[str, str]` — per-task re-wording of tool descriptions
  (the agent sees these, not the generic registration descriptions).
- `def repair_feedback(failures, output) -> str` — custom message fed back to
  the model on verify failure. Default is a generic message.

All optional. Each is bounds-clamped on load; wrong types silently fall back to
defaults. The executor honors every field — no more hardcoded loop config.

### Added — Gemini provider
- `aegis.providers.Gemini` — Google Gemini adapter using the official
  `google-genai` SDK. Maps Aegis's internal Message shape onto Gemini's
  Content/Part/FunctionResponse model. Install with
  `pip install self-harness[gemini]`. Auto-detected via `GOOGLE_API_KEY` /
  `GEMINI_API_KEY` env vars.

### Changed
- Synthesize prompt rewritten to teach the LLM the full v0.3 contract with
  worked example and explicit hard rules. Real-LLM testing showed this reduces
  first-attempt sandbox-load failures meaningfully.
- Fallback Jinja template emits the full contract too (with `SYSTEM_PROMPT`,
  `MAX_STEPS`, `MAX_REPAIRS`, `repair_feedback`).
- `render_fallback()` sizes `MAX_STEPS` and `MAX_REPAIRS` to the risk profile
  weight — high-risk goals get more steps and more repairs.

### Fixed (carried from 0.2.x development)
- Synthesize retry loop now exercises `load_harness()` not just `validate_source()`,
  so pydantic schema errors (e.g. leading-underscore field names) trigger a retry
  with corrective feedback instead of crashing later.
- Pipeline gracefully falls back to the deterministic template when
  `load_harness()` fails after all generator retries.
- Pydantic v2 forward-ref resolution: `Output.model_rebuild(_types_namespace=…)`
  called after exec so `Any`, `Literal`, custom types resolve against the
  harness's own namespace (synthetic `__module__` isn't in `sys.modules`).

### Tests
- **58 unit tests** (was 50). New module `test_harness_contract_v03.py` covers
  defaults, bounds clamping, type coercion, and pipeline honoring harness-emitted
  `MAX_REPAIRS`.

---

## [0.2.0] — 2026-05-22

### Fixed (correctness)
- **Multi-turn tool calls now work against real LLMs.** v0.1 appended an assistant
  message without the `tool_calls` field, which caused OpenAI to reject the very
  next request with `400: messages with role 'tool' must be a response to a preceeding
  message with 'tool_calls'`. Anthropic had the symmetric bug in its content-block
  shape. The internal `Message` type now carries a `tool_calls` list and
  `Message.tool_result(...)` factory, and the two adapters serialize correctly.
- OpenAI adapter switched from `max_tokens` to `max_completion_tokens`, which is
  required by the gpt-5 / o-series models and accepted by gpt-4o.
- Web demo: the `_suppress` context manager (which silently dropped exceptions
  from `await ws.close()`) replaced with `contextlib.suppress`. Cleanup logic
  now runs in `finally`.

### Added
- **Sandbox wall-clock + memory limits.** `verify()` runs under `signal.ITIMER_REAL`
  for sub-second timeout and `resource.setrlimit(RLIMIT_AS)` for a memory cap.
  POSIX only; Windows falls back to plain execution with a warning. New
  `SandboxTimeout` exception, and `HarnessModule.call_verify(timeout_s, memory_mb)`.
- **Streaming for the OpenAI provider** — `Provider.stream()` yields `("delta", str)`
  events as tokens arrive, finishing with `("done", Completion)`. Web demo
  ready to consume (UI hookup planned for v0.3).
- **Retry + rate-limit handling** in both Anthropic and OpenAI adapters
  (exponential backoff: 1s → 2s → 4s → 8s → 16s, max 3 retries by default).
- **VCR-recorded integration tests** scaffold (`tests/integration/`) with
  cassette redaction of `Authorization` / `x-api-key` / cookies.
- **Live-validation script** (`scripts/run_live.py`) — single command, 7 checks,
  exits non-zero on any failure. Use this to gate releases.
- Tests for multi-turn Message serialization (both OpenAI and Anthropic
  shapes) and sandbox limit enforcement. **48 unit tests** total (was 36).

### Changed
- Synthesize-stage system prompt tightened: explicit allowlist of imports,
  explicit forbidden constructs, required interface contract spelled out,
  example shape provided. Goal is to make first-attempt sandbox-valid
  generation reliable.
- `Provider` protocol unchanged; new helpers `to_openai_dicts(...)` and
  `to_anthropic(...)` in `providers.base` for the serialization layer.

### Security notes
- The sandbox is appropriate for trusted local execution. **It is not a
  multi-tenant security boundary.** For untrusted goals, run Aegis inside a
  process sandbox (firejail, Docker, gVisor).

---

## [0.1.0] — 2026-05-22

Initial release. 5-stage pipeline, 30-entry risk catalog, four provider
adapters (Anthropic, OpenAI, Ollama, LiteLLM, Mock), CLI, FastAPI web demo,
mkdocs site, MIT license. Verified end-to-end against the Mock provider only.
Known caveats addressed in 0.2.0.
