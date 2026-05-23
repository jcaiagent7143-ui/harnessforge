# Release checklist — harnessforge v0.2.1

Everything below requires your accounts or your decisions. Steps in
order — do not skip.

## 1. Reserve the GitHub repo (one command, your account)

```bash
gh repo create harnessforge --public \
  --description "Universal harness layer for AI coding agents — one command sets up your repo for Claude Code, Cursor, Codex, Gemini CLI, Aider, OpenHarness." \
  --homepage "https://jcaiagent7143-ui.github.io/harnessforge"
```

Output should include `https://github.com/jcaiagent7143-ui/harnessforge`.

## 2. Reserve the PyPI name (one command, your account)

PyPI doesn't have a "reserve" flow — the name is yours the moment you
successfully upload the first release. So this step actually happens at
step 6. To pre-flight that the name is available, hit:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/harnessforge/json
# 404 = available  /  200 = taken
```

If 200, we rename. Tell me and I'll switch every reference to a free name.

## 3. Set up PyPI Trusted Publishing (one-time, in the PyPI web UI)

`harnessforge` doesn't exist on PyPI yet, so use the **pending publisher**
flow (which works before the first upload):

1. Sign in at `https://pypi.org/manage/account/publishing/`
2. Scroll to "Add a new pending publisher"
3. Fill in exactly:
   - **PyPI project name**: `harnessforge`
   - **Owner**: `jcaiagent7143-ui`
   - **Repository name**: `harnessforge`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`
4. Click **Add**

Then in GitHub:

1. Repo Settings → Environments → **New environment** → name: `pypi`
2. (Optional, recommended) Add yourself under **Required reviewers** —
   so every PyPI publish gets a one-click human approval.

## 4. Commit + push everything (I'll prepare the commit; you run it)

From the repo root:

```bash
# Add the existing remote for the new repo (keep aegis as a fork-of-history reference)
git remote add harnessforge https://github.com/jcaiagent7143-ui/harnessforge.git

# Stage everything we've changed this session
git add -A

# Commit — message below captures the v0.1 → v0.2 → v0.2.1 arc honestly
git commit -m "$(cat <<'EOF'
feat(harnessforge 0.2.1): real-build eval-driven release-ready

Rebrand self-harness → harnessforge, add 2 blueprints (python-cli-app +
finance-agent), and ship 12 surgical fixes caught by two rounds of
real-agent A/B evaluations (Claude Code building a stock-analysis agent
WITH vs. WITHOUT the harness).

v0.2 (closes 7 strategic gaps from the v0.1 eval):
- python-cli-app blueprint (the 80% case)
- finance-agent blueprint with no_trades_without_gate validator
- SKILLS/domain/ for project-specific procedures
- Inspector-driven pruning of forbidden_paths/MCPs/approval list
- Smart test-runner detection (no more null test_command)
- harness verify --tests/--lint shortcuts
- Build-mode SOUL persona

v0.2.1 (closes 5 polish gaps from v0.2 eval):
- python vs python3 detection (was breaking macOS first-run)
- Memory schemas now actually copied into user repo (.harness/memory_schemas/)
- Blueprint-level MCP pruning + dedup (no more "filesystem listed twice")
- forbidden_commands pruning (no more kubectl recommended for portfolio CLI)
- Trust-model documentation

Quality: 186 tests passing (vs 129 in v0.1), 83% coverage on src/harness/,
mypy strict + ruff clean, mkdocs --strict clean, fresh-venv install verified
end-to-end (caught + fixed missing PyYAML runtime dep along the way).

Also includes: GitHub repo URL refresh, hero demo SHA pinning, Trusted
Publishing OIDC release.yml, security policy, code of conduct, contributing
guide, bug + feature issue templates, demo.tape for the README GIF.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"

# Push to the new repo as the primary remote
git push -u harnessforge main
```

If you'd rather keep the existing `aegis` repo as primary (and rename
*it* on GitHub instead of creating a new repo), say so — that's one
"Rename this repository" click in GitHub Settings + a `git remote set-url
origin` and we're done. Cleaner history, no broken `aegis` URL refs.

## 5. (Optional but recommended) Generate the demo GIF

```bash
brew install vhs
vhs docs/assets/demo.tape   # writes docs/assets/demo.gif (~800KB)

# Then add it to the README hero block:
git add docs/assets/demo.gif
git commit -m "docs: add README hero demo GIF"
git push
```

## 6. Tag + publish to PyPI

Once steps 1-4 are done and the repo is green on GitHub:

```bash
# Tag this commit (the workflow accepts both v* and harnessforge-v* shapes)
git tag harnessforge-v0.2.1
git push harnessforge harnessforge-v0.2.1
```

GitHub Actions:
1. Builds sdist + wheel from the tagged commit
2. Waits for environment approval (if you set Required reviewers in step 3)
3. OIDC-uploads to PyPI as `harnessforge-0.2.1`
4. Creates a GitHub Release with the CHANGELOG section auto-extracted

Watch the workflow live: `gh run watch`

## 7. Post-release verification (5 min)

```bash
# In a fresh shell on any machine:
pip install harnessforge
harness version          # should print: harnessforge 0.2.1
harness blueprint list   # should show 5 blueprints
mkdir /tmp/postlaunch && cd /tmp/postlaunch
echo "# x" > README.md && printf '[project]\nname = "x"\nversion = "0.1"\n' > pyproject.toml
harness init --no-llm    # should write 17 files
harness verify --json    # should print the stable JSON contract
```

## 8. Launch announcement (when you're ready)

Drafts are pre-written in `LAUNCH.md` for HN, Twitter/X, and r/LocalLLaMA.
Don't ship them until step 7 passes on a machine that isn't yours.

---

## What's NOT in v0.2.1 (deferred)

- **Windows test** — explicitly skipped per your call
- **Docs site deployed to GitHub Pages** — workflow exists at
  `.github/workflows/docs.yml`, will auto-fire on first push to main
- **Hero demos in CI nightly against real repos** — workflow exists at
  `.github/workflows/hero.yml`, will fire on every push (uses pinned SHAs)
- **Skills hub integration** — `agentskills.io` sync — v0.3
- **sales-agent / browser-agent blueprints** — need auth-bearing MCPs — v0.3

## If anything fails post-tag

```bash
# Delete the tag (locally + remote) and try again
git tag -d harnessforge-v0.2.1
git push harnessforge :refs/tags/harnessforge-v0.2.1
```

Then fix + push + retag.

PyPI **does not allow re-uploading** a deleted version. If 0.2.1 makes
it to PyPI broken, the next release is `0.2.2` — not a re-upload of
0.2.1. Plan accordingly.
