"""`harness mcp` — run the stdio MCP server exposing harness tools."""

from __future__ import annotations

import typer
from rich.console import Console

console = Console()


def run() -> None:
    """Run harness as a Model Context Protocol (stdio) server.

    Any MCP client (Claude Desktop, Claude Code, Cursor, Cline, Continue,
    Windsurf, ...) can spawn this process and call the harness tools:

      * harness_inspect       — InspectionReport JSON
      * harness_blueprint_list — installed blueprints
      * harness_skills_list   — local SKILLS/ + catalog
      * harness_verify        — run validators (same contract as `harness verify --json`)
      * harness_profile_read  — current .harness/profile.yaml

    Typical Claude Desktop config:

        {
          "mcpServers": {
            "harness": {"command": "uvx", "args": ["harnessforge", "mcp"]}
          }
        }
    """
    try:
        from harness.mcp.server import run_stdio
    except ImportError as e:
        console.print(r"[red]Install MCP extras: pip install 'harnessforge\[mcp]'[/red]")
        raise typer.Exit(code=2) from e
    run_stdio()
