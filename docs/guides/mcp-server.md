# MCP server

`harness mcp` exposes the harness as a Model Context Protocol (stdio) server. Any MCP client can spawn it and call the harness as typed tools.

## What it exposes

| Tool | Returns |
|---|---|
| `harness_inspect(path?)` | InspectionReport JSON |
| `harness_blueprint_list()` | Array of installed blueprints with metadata |
| `harness_skills_list(path?)` | Local SKILLS/ + catalog skills |
| `harness_verify(path?, check?, fail_fast?)` | Same JSON as `harness verify --json` |
| `harness_profile_read(path?)` | Parsed `.harness/profile.yaml` |

If a `path` argument is omitted, the server uses `$HARNESS_ROOT` env var, or the CWD.

## Install

```bash
pipx install 'harnessforge[mcp]'
```

## Wire it up

### Claude Desktop

`~/.config/claude-desktop/config.json` (mac) or `%APPDATA%\Claude\config.json` (Windows):

```json
{
  "mcpServers": {
    "harness": {
      "command": "uvx",
      "args": ["--from", "harnessforge[mcp]", "harness", "mcp"]
    }
  }
}
```

### Cursor

`~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "harness": {
      "command": "harness",
      "args": ["mcp"]
    }
  }
}
```

### Cline / Continue / Windsurf

Same shape — pick whatever MCP config the IDE expects, point it at `harness mcp`.

## Use from a coding agent

Once connected, your agent has typed access. Examples:

```
agent: I'd like to verify this repo before answering. Calling harness_verify…
result: {"summary": {"total": 3, "passed": 2, "failed": 1}, "checks": [...]}
agent: The citations validator failed because chunk_id 'abc' was orphaned. Let me fix that.
```

The agent reads the JSON output, decides what to do, and may retry.

## Env

| Var | Purpose |
|---|---|
| `HARNESS_ROOT` | Default repo path for tools that take `path` |
