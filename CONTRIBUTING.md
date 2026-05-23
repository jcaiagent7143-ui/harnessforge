# Contributing to harnessforge

Thanks for taking the time to look. This doc gets you from `git clone` to
a green PR in under 15 minutes.

## TL;DR

```bash
git clone https://github.com/jcaiagent7143-ui/harnessforge.git
cd harnessforge
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,proxy,mcp,openai]"
pytest tests/harness         # 186+ tests; runs in ~4s
ruff check src/harness tests/harness
mypy src/harness             # strict mode
mkdocs build --strict        # docs (optional)
```

If all four pass, you're set up.

The extras above pull in everything contributors need:

- `dev`     — pytest, ruff, mypy, types-PyYAML (required to run the suite)
- `mcp`     — the `mcp` SDK; required to touch `harness.mcp.server`
- `openai`  — the openai SDK; required for `aegis.providers.openai` tests
- `proxy`   — fastapi + uvicorn; required for the aegis OpenAI-compatible
  proxy tests (the only reason it's in the contributor install — end users
  never need it)

If you're only fixing docs or a blueprint template, the smaller
`pip install -e ".[dev]"` is enough.

## The repo layout

```
src/harness/                # the public face — what `harness init` ships
  adapters/                 # IDE adapters (claude, cursor, codex, continue, windsurf)
  blueprints/<name>/        # one directory per blueprint (rag-agent, finance-agent, ...)
    blueprint.yaml          # spec
    files/                  # Jinja2 templates rendered into the user's repo
    skills/<name>/SKILL.md  # anthropics/skills-compatible
    validators/             # Python; run inside aegis sandbox
    memory_schemas/         # JSON Schema
    eval/                   # eval question set
  catalog/mcps.yaml         # curated MCP server registry
  cli/                      # typer CLI (init/sync/verify/blueprint/skills/...)
  inspect_/                 # deterministic repo walker (no LLM)
  profile.py                # HarnessProfile + template + LLM-driven profilers
  provision.py              # the inspect → profile → blueprint → render orchestrator
  validators/               # validator runner (loads blueprint validators safely)

src/aegis/                  # internal LLM I/O + sandbox + cache layer
                            # used by harness.profile and harness.validators

tests/harness/
  unit/                     # mocked-LLM unit tests
  golden/                   # snapshot tests of generated trees
  interop/                  # anthropics/skills format conformance
  integration/              # CLI subprocess tests

docs/                       # mkdocs-material site
examples/hero/              # reproducible end-to-end demos
```

## Common contribution flows

### Add a new blueprint

1. Make a new directory under `src/harness/blueprints/<name>/` matching
   the [Blueprint schema](docs/reference/blueprint-schema.md) reference.
2. Drop `blueprint.yaml`, `README.md`, templates under `files/`,
   skill bundles under `skills/<skill>/SKILL.md`, validator modules
   under `validators/`, JSON Schemas under `memory_schemas/`, and an
   eval set under `eval/`.
3. Add the blueprint to the recommender heuristic in
   `src/harness/blueprints/loader.py::recommend_blueprint` if it should
   ever be picked automatically.
4. Extend the parametrized tests in `tests/harness/unit/test_blueprints.py`,
   `tests/harness/unit/test_provision.py`, and
   `tests/harness/interop/test_skills_format.py` to include your name.
5. Update `docs/blueprints/index.md` and add `docs/blueprints/<name>.md`.

The shipped 5 blueprints are good reference implementations — copy the
closest one.

**Acceptance bar for a new blueprint** (so PRs don't sit forever):

- The blueprint covers an *agent type*, not a project type (i.e. "the
  agent does X" — `browser-agent`, `sales-agent` — not "for Django
  projects"). Project-type tailoring belongs in `profile.yaml`, not in
  the blueprint.
- The skills under `skills/` each have a concrete "Failure modes to
  avoid" section. Three of the v0.2 stock-agent eval's "wow, this
  actually saved me from a real bug" moments came from this section;
  it's the highest-signal contribution in a PR.
- At least one validator that *actually fails* on plausibly-broken
  output (e.g. `finance-agent`'s `no_trades_without_gate` scanner;
  `rag-agent`'s citation cross-checker). Validators that only ever
  return `[]` aren't pulling weight.
- A README under `src/harness/blueprints/<name>/README.md` with a
  "When to use" + "When NOT to use" section — the latter matters more
  than the former.
- Goldens regenerated (`pytest tests/harness/golden/ --update-goldens`).

If you're unsure whether your idea fits, **open an issue with the label
`blueprint-proposal` first**. Better to align on shape before you write
500 lines of templates we'd ask you to rework.

### Fix a bug

1. **Write a regression test first.** `tests/harness/unit/test_v021_patch.py`
   shows the pattern — one test per surgical fix, named for the issue.
2. Make the fix.
3. Run the full suite: `pytest tests/harness/ -q --cov=src/harness`.
4. If the fix changes the on-disk shape of `harness init` output, update
   golden snapshots: `pytest tests/harness/golden/ --update-goldens`.
5. Add an entry to `CHANGELOG.md` under "Fixed".

### Improve a validator

Validators are plain Python that return `list[str]` (failure messages).
Empty list = pass. Messages starting with `"SKIPPED:"` are treated as
skipped (not failure). They run inside the aegis AST-allowlist sandbox,
so you can't use `subprocess` unless you're explicitly allowed (see
`src/aegis/synthesize/sandbox.py`).

### Improve a skill

`SKILLS/<name>/SKILL.md` follows the
[`anthropics/skills`](https://github.com/anthropics/skills) format. The
**Failure modes to avoid** section is the highest-value part — the
v0.2 stock-agent eval showed that 3 of the SKILL files prevented real
bugs an agent would have made on a bare repo, and each one was caught
by a "failure mode" section warning.

## The trust model (one paragraph; full doc is `docs/concepts/trust-model.md`)

`harness verify --tests` and `harness verify --lint` execute the strings
in `profile.test_command` / `profile.lint_command` via `subprocess.run`,
with the user's privileges, in the user's CWD. Same trust model as
`make test` or `npm test`: the profile.yaml is *code*, treat it the way
you'd treat a `Makefile` from the same source. Everything else in the
profile — `forbidden_paths`, `forbidden_commands`, `requires_human_approval`,
`conventions`, `success_criteria`, MCP names — is data the agent reads,
never executed. Blueprint validators are package code (not user code) and
run inside the aegis AST-allowlist sandbox.

If your change touches `harness.validators`, `harness.provision`, or
`profile_from_inspection_template`, you're in security territory — read
the full trust-model doc first.

## Test tiers

| Tier | When it runs | What it tests |
|---|---|---|
| unit | every pytest | logic — inspect/profile/blueprints/validators/skills_io with mocked LLM |
| golden | every pytest | snapshot of generated path-set per (fixture-repo × blueprint) |
| interop | every pytest | anthropics/skills format conformance + JSON Schema validity |
| integration | every pytest (if `harness` binary on PATH) | drives the actual `harness` CLI via subprocess |
| hero demos | CI on push | clone real public repos at pinned SHAs, `harness init`, `harness verify` |

## Style

- **ruff** in CI — `ruff check src/harness tests/harness` must be clean
- **mypy strict** in CI — `mypy src/harness` must pass with `disallow_untyped_defs`
- **Type hints everywhere** in `src/harness/`
- **Docstrings on public functions** — at minimum a one-line summary
- **No `# noqa`** without a justification comment on the same line
- **Match the surrounding style** before adding new patterns

## What we don't do

- **No emojis in code or commits** unless the project already uses them somewhere
- **No `requirements.txt`** — `pyproject.toml` `[project.dependencies]` is the source of truth
- **No `setup.py`** — hatchling only
- **No `# type: ignore` without a `[code]`** specifier
- **No silent failures in validators** — surface SKIPPED with a reason
- **No new top-level CLI commands** without first opening an issue to discuss

## PR checklist

- [ ] Tests pass (`pytest tests/harness/`)
- [ ] ruff clean (`ruff check src/harness tests/harness`)
- [ ] mypy strict clean (`mypy src/harness`)
- [ ] mkdocs builds (`mkdocs build --strict`) if you touched docs
- [ ] CHANGELOG entry under the right section (Added / Fixed / Changed)
- [ ] If you added a blueprint, all four files exist: `blueprint.yaml`,
      at least one template, at least one validator, at least one skill

## Releases

Maintainers cut releases via the tag `harnessforge-vX.Y.Z`. Trusted
Publishing pushes to PyPI on tag — no API tokens in repo.

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). Be kind.

## License

MIT — see [LICENSE](LICENSE). Contributions are licensed the same.
