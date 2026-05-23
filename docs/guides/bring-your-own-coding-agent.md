# Bring your own coding agent

Harness Kit generates files that every major coding agent already knows how to read. Zero per-IDE config required.

## Claude Code

Reads `.claude/CLAUDE.md` automatically on session start. No setup needed.

## Cursor

Reads `.cursor/rules` automatically. If you also want `harness verify` available as a tool, connect the MCP server (see below).

## Codex CLI (OpenAI)

Reads `AGENTS.md` at the repo root. Standard.

## Continue

Reads `.continue/config.json`. The harness adapter sets `systemMessage` + the project's recommended MCP servers.

## Windsurf

Reads `.windsurf/rules`. Same shape as Cursor — sections for "always follow", "never touch", "never run", etc.

## Gemini CLI

Reads `AGENTS.md`. Same as Codex CLI.

## Aider

Reads `AGENTS.md` and the project's `CONTRIBUTING.md`. Works out of the box.

## OpenHarness

Discovers `MEMORY.md`, `CLAUDE.md`, and `SKILLS/` automatically. Run `oh` from the repo root and it picks them up.

## Hermes / OpenClaw

Both read `SOUL.md` and the `SKILLS/` directory (anthropics/skills format). Drop the agent in the repo and it picks up the right tone + procedures.

## Connect `harness mcp`

For typed tool access from any MCP client:

```json
// ~/.config/claude-desktop/config.json or ~/.cursor/mcp.json
{
  "mcpServers": {
    "harness": {
      "command": "uvx",
      "args": ["--from", "harness-kit[mcp]", "harness", "mcp"]
    }
  }
}
```

The MCP server exposes:

- `harness_inspect` — full InspectionReport JSON
- `harness_blueprint_list` — installed blueprints
- `harness_skills_list` — local + catalog skills
- `harness_verify` — run validators (same JSON as `harness verify --json`)
- `harness_profile_read` — parsed `.harness/profile.yaml`

Your coding agent can call any of these as a typed tool.
