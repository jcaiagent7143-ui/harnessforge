"""harness CLI entry point — `harness {init,sync,inspect,verify,blueprint,skills,doctor,mcp,version}`.

This module wires every subcommand into a single ``typer`` app. Each
subcommand lives in its own file (e.g. ``harness.cli.init``) so the
import surface stays small.
"""

from __future__ import annotations

import typer
from rich.console import Console

from harness.cli import (
    blueprint as blueprint_cmd,
)
from harness.cli import (
    doctor as doctor_cmd,
)
from harness.cli import (
    init as init_cmd,
)
from harness.cli import (
    inspect as inspect_cmd,
)
from harness.cli import (
    mcp as mcp_cmd,
)
from harness.cli import (
    skills as skills_cmd,
)
from harness.cli import (
    sync as sync_cmd,
)
from harness.cli import (
    verify as verify_cmd,
)
from harness.cli import (
    version as version_cmd,
)

app = typer.Typer(
    name="harness",
    help=(
        "harnessforge — the universal harness layer for AI coding agents.\n\n"
        "One command sets up your repo so Claude Code, Cursor, Codex, "
        "Gemini CLI, Aider, OpenHarness, and any other coding agent can "
        "work in it productively."
    ),
    no_args_is_help=True,
    add_completion=False,
)

console = Console()

# Top-level commands
app.command("init")(init_cmd.run)
app.command("sync")(sync_cmd.run)
app.command("inspect")(inspect_cmd.run)
app.command("verify")(verify_cmd.run)
app.command("doctor")(doctor_cmd.run)
app.command("mcp")(mcp_cmd.run)
app.command("version")(version_cmd.run)

# Sub-typers
app.add_typer(blueprint_cmd.app, name="blueprint", help="Manage harness blueprints.")
app.add_typer(skills_cmd.app, name="skills", help="Manage anthropics/skills-compatible skills.")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
