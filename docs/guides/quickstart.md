# Quickstart

## Three commands

```bash
# 1. Run init in your repo (no install needed)
uvx harness-kit init --no-llm

# 2. See what got written
ls -A | grep -E '^(AGENTS|SOUL|TOOLS|MEMORY)\.md$|^SKILLS|^harness.config|^.harness'

# 3. Verify
uvx harness-kit verify --json
```

## What `init` does

1. Walks the repo and runs `inspect_repo` (deterministic, no LLM).
2. Builds a `HarnessProfile` — your project's name, type, language, commands, forbidden paths.
3. Picks a blueprint (`rag-agent`, `support-agent`, or `workflow-agent`) based on the inspection.
4. Renders five IDE adapter files (`.claude/CLAUDE.md`, `.cursor/rules`, `.continue/config.json`, `.windsurf/rules`, `AGENTS.md`).
5. Renders the blueprint's `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `MEMORY.md`, scripts, and SKILLS.
6. Writes a `harness.config.json` and `.harness/manifest.json` for safe re-runs.

## Pick a specific blueprint

```bash
uvx harness-kit init --blueprint rag-agent
uvx harness-kit init --blueprint support-agent
uvx harness-kit init --blueprint workflow-agent
```

## Use a specific LLM as the profiler

```bash
export ANTHROPIC_API_KEY=...
pip install 'harness-kit[anthropic]'
harness init                           # uses Claude to refine the profile
```

Or skip the LLM entirely:

```bash
harness init --no-llm                  # deterministic; no API key needed
```

## Dry-run

```bash
harness init --dry-run                 # shows the plan; writes nothing
```

## Re-render after editing the profile

```bash
# Edit .harness/profile.yaml by hand, then:
harness sync                           # re-renders adapter + blueprint files
harness sync --check                   # CI mode: exit 1 if anything drifted
```

## Next

- [Bring your own coding agent](bring-your-own-coding-agent.md) — wire harness output into Claude Code, Cursor, etc.
- [MCP server](mcp-server.md) — connect `harness mcp` to any MCP client.
- [Authoring a custom skill](authoring-a-skill.md) — extend SKILLS/ with project-specific procedures.
