"""`harness blueprint` — list / show / apply a blueprint."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harness.provision import provision_sync

app = typer.Typer(help="Manage harness blueprints.", no_args_is_help=True)
console = Console()


@app.command("list")
def list_blueprints() -> None:
    """List installed blueprints."""
    from harness.blueprints import list_blueprints as _list

    bps = _list()
    if not bps:
        console.print("[yellow]No blueprints installed.[/yellow]")
        return
    t = Table(title=f"Blueprints ({len(bps)})")
    t.add_column("name", style="cyan")
    t.add_column("version", style="dim")
    t.add_column("type")
    t.add_column("description")
    for bp in bps:
        t.add_row(bp.name, bp.version, bp.agent_type, bp.description)
    console.print(t)


@app.command("show")
def show_blueprint(
    name: str = typer.Argument(..., help="Blueprint name (e.g. rag-agent)."),
) -> None:
    """Print the YAML spec for one blueprint."""
    from harness.blueprints import load_blueprint

    try:
        bp = load_blueprint(name)
    except KeyError as e:
        console.print(f"[red]{e}[/red]")
        raise typer.Exit(code=2) from e

    console.print(Panel(f"[bold]{bp.display_name}[/bold] · `{bp.name}` v{bp.version}"))
    console.print(f"[dim]description:[/dim] {bp.description}")
    console.print(f"[dim]agent type:[/dim] {bp.agent_type}")
    console.print(f"[dim]recommended MCPs:[/dim] {', '.join(bp.recommended_mcps) or '—'}")
    console.print(f"[dim]memory schemas:[/dim] {', '.join(bp.memory_schemas) or '—'}")
    if bp.skills:
        console.print(f"[dim]skills:[/dim] {', '.join(bp.skills)}")
    if bp.validators:
        t = Table(title="Validators")
        t.add_column("name", style="cyan")
        t.add_column("description")
        for v in bp.validators:
            t.add_row(v["name"], v.get("description", ""))
        console.print(t)
    if bp.generated_files:
        t = Table(title="Files this blueprint generates")
        t.add_column("path", style="cyan")
        t.add_column("template", style="dim")
        for f in bp.generated_files:
            t.add_row(f.path, f.template)
        console.print(t)


@app.command("apply")
def apply_blueprint(
    name: str = typer.Argument(..., help="Blueprint name to apply."),
    path: Path = typer.Argument(Path("."), help="Repo to apply into."),
    force: bool = typer.Option(False, "--force", "-f"),
    no_skills: bool = typer.Option(False, "--no-skills"),
) -> None:
    """Apply a blueprint to a repo (re-run init with this blueprint)."""
    result = provision_sync(
        path,
        blueprint=name,
        no_llm=True,
        force=force,
        no_skills=no_skills,
    )
    console.print(
        f"[green]✓ applied {result.plan.blueprint_name} v{result.plan.blueprint_version}: "
        f"{len(result.written)} files written[/green]"
    )
