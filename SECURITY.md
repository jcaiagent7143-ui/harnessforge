# Security Policy

## Supported versions

The latest minor release (`harnessforge 0.2.x`) is supported with
security fixes. Older versions and the legacy `self-harness` distribution
are not.

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a vulnerability

**Do not** open a public GitHub issue for security vulnerabilities.

Use GitHub's private security advisory form:

→ `https://github.com/jcaiagent7143-ui/harnessforge/security/advisories/new`

Or, if you can't use GitHub's flow, send a private message to the
maintainer.

You can expect:

- Acknowledgement within 5 working days.
- A coordinated disclosure timeline once we agree on the scope of the fix.
- Credit in the changelog (unless you'd rather stay anonymous).

## What's in scope

- Sandbox escapes in `aegis.synthesize.sandbox` (a blueprint validator that
  escapes the AST allowlist + restricted exec to read/write outside the
  user's repo, execute shell commands, exfiltrate env vars, etc.).
- Path-traversal in the manifest / collision policy in `harness.provision`
  (writing outside the user's `repo_root`).
- Auth-token handling in `harness mcp` (leaking tokens to clients).
- Vulnerabilities in the shipped MCP catalog (`harness.catalog.mcps`).
- Dependency vulnerabilities surfaced by `pip-audit` / Dependabot.

## What's NOT in scope (read the trust model first)

`profile.test_command` and `profile.lint_command` are executed as shell
commands by `harness verify --tests` and `harness verify --lint`. This
is by design — they're how the project runs its own tests and linter.

A maliciously-crafted `profile.yaml` that includes a destructive
`test_command` is the same threat as a malicious `Makefile`,
`npm test` script, or `pytest` plugin in `pyproject.toml`. **Trust the
profile the same way you'd trust the rest of the repo.**

See [`docs/concepts/trust-model.md`](docs/concepts/trust-model.md) for
the full trust-boundary discussion. Reports along the lines of
"a malicious profile.yaml runs arbitrary commands" will be closed as
working-as-intended; the trust boundary is the git commit that added
the profile, not the harness.

Also out of scope:

- DoS via expensive `harness init` runs on enormous repos — set a
  `--max-files` flag for your CI if you need that constraint; the
  inspector caps at 5000 files by default.
- Issues that require physical access to the host or root privileges.

## Hardening notes for production / CI deployments

- **CI on external PRs**: run `harness verify` in an ephemeral runner
  (GitHub Actions on `pull_request` does this by default for first-time
  contributors). Don't run external-PR validators in a long-lived runner
  with secrets attached.
- **Pin harnessforge** in your CI's `requirements.txt` so a supply-chain
  compromise of a future harnessforge release doesn't auto-apply.
- **Audit `profile.yaml` diffs in PR review** — `test_command` /
  `lint_command` changes are the only privileged fields.
- **`harness mcp`** runs over stdio; treat the spawned process the same
  way you'd treat any MCP server (the client decides which tools to call;
  the server only does what it advertises).
