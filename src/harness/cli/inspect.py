"""`harness inspect` — print the deterministic repo inspection report."""

from __future__ import annotations

import json
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.table import Table

from harness.inspect_ import inspect_repo

console = Console()


def run(
    path: Path = typer.Argument(Path("."), help="Repo to inspect. Defaults to CWD."),
    output: str = typer.Option(
        "table",
        "--format",
        "-f",
        help="Output format: table | json | yaml.",
    ),
) -> None:
    """Walk a repo and print what we learn (deterministic, no LLM)."""
    if output not in {"table", "json", "yaml"}:
        console.print("[red]--format must be table | json | yaml[/red]")
        raise typer.Exit(code=2)

    report = inspect_repo(path)
    data = report.to_prompt_dict()

    if output == "json":
        print(json.dumps(data, indent=2, default=str))
        return
    if output == "yaml":
        print(yaml.safe_dump(data, sort_keys=False, width=100))
        return

    # table
    console.rule(f"[bold]harness inspect[/bold] · {report.root.name}")
    t = Table(show_header=False, box=None, padding=(0, 1))
    t.add_row("[dim]languages[/dim]", ", ".join(data["languages"]) or "—")
    t.add_row("[dim]frameworks[/dim]", ", ".join(data["frameworks"]) or "—")
    t.add_row("[dim]package mgrs[/dim]", ", ".join(data["package_managers"]) or "—")
    t.add_row("[dim]tests[/dim]", " | ".join(data["test_commands"]) or "—")
    t.add_row("[dim]lint[/dim]", " | ".join(data["lint_commands"]) or "—")
    t.add_row("[dim]build[/dim]", " | ".join(data["build_commands"]) or "—")
    t.add_row(
        "[dim]ci[/dim]",
        data["ci"]["provider"] if data["ci"]["enabled"] else "—",
    )
    t.add_row(
        "[dim]container[/dim]",
        ", ".join(
            k for k, v in data["containerization"].items() if v
        ) or "—",
    )
    t.add_row(
        "[dim]git[/dim]",
        data["git"]["remote"] or "—",
    )
    t.add_row(
        "[dim]env vars[/dim]",
        ", ".join(data["env_vars_expected"][:6])
        + (" …" if len(data["env_vars_expected"]) > 6 else "")
        or "—",
    )
    t.add_row(
        "[dim]existing[/dim]",
        ", ".join(data["existing_agent_configs"]) or "—",
    )
    t.add_row("[dim]MCPs found[/dim]", ", ".join(data["detected_mcps"]) or "—")
    t.add_row("[dim]files[/dim]", str(data["scale"]["file_count"]))
    t.add_row("[dim]lines (~)[/dim]", str(data["scale"]["line_count_approx"]))
    console.print(t)
