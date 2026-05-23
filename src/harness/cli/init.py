"""`harness init` — inspect the repo, pick a blueprint, write everything."""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harness.provision import provision_sync

console = Console()


def run(
    path: Path = typer.Argument(Path("."), help="Repo to bootstrap. Defaults to CWD."),
    blueprint: str | None = typer.Option(
        None,
        "--blueprint",
        "-b",
        help="Pick a blueprint explicitly (rag-agent / support-agent / workflow-agent). "
        "If omitted, harness recommends one based on the inspection.",
    ),
    no_llm: bool = typer.Option(
        False,
        "--no-llm",
        help="Skip the LLM-based profiler — use the deterministic template only. "
        "No API key required. Recommended for CI.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files even if they've been hand-edited.",
    ),
    adapters: str | None = typer.Option(
        None,
        "--adapter",
        help="Comma-separated IDE adapters (e.g. claude-code,cursor). Default: all.",
    ),
    no_skills: bool = typer.Option(
        False,
        "--no-skills",
        help="Skip rendering anthropics/skills-compatible SKILLS/ directory.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be written, but write nothing.",
    ),
) -> None:
    """Inspect the repo and bootstrap a complete harness."""
    adapter_list = [a.strip() for a in adapters.split(",")] if adapters else None

    with console.status("[bold cyan]inspecting repo & building plan...", spinner="dots"):
        result = provision_sync(
            path,
            blueprint=blueprint,
            no_llm=no_llm,
            force=force,
            adapters=adapter_list,
            no_skills=no_skills,
            dry_run=dry_run,
        )

    _render(result)
    if not dry_run and result.skipped and not force:
        raise typer.Exit(code=1)


def _render(result: object) -> None:
    from harness.provision import ProvisionResult  # local import to avoid cycle

    if not isinstance(result, ProvisionResult):  # defensive
        console.print(result)
        return

    plan = result.plan
    badge = "[yellow](dry-run)[/yellow]" if result.dry_run else "[green]✓[/green]"
    console.rule(f"[bold]harness init[/bold] {badge}")

    summary = Table(show_header=False, box=None, padding=(0, 1))
    summary.add_row("[dim]project[/dim]", plan.profile.name)
    summary.add_row("[dim]type[/dim]", plan.profile.project_type)
    summary.add_row("[dim]language[/dim]", plan.profile.primary_language)
    if plan.profile.frameworks:
        summary.add_row("[dim]frameworks[/dim]", ", ".join(plan.profile.frameworks))
    summary.add_row("[dim]blueprint[/dim]", f"{plan.blueprint_name} v{plan.blueprint_version}")
    console.print(Panel(summary, title="profile"))

    files = Table(title=f"files ({len(plan.files)})")
    files.add_column("path", style="cyan")
    files.add_column("by", style="dim")
    files.add_column("bytes", justify="right")
    for pf in plan.files:
        rel = pf.path.relative_to(plan.repo_root)
        files.add_row(str(rel), pf.written_by, str(len(pf.content)))
    console.print(files)

    if not result.dry_run:
        console.print(f"\n[green]wrote {len(result.written)} files[/green]")
    if result.skipped:
        console.print(
            f"[yellow]skipped {len(result.skipped)} files[/yellow] (already on disk; "
            f"use --force to overwrite)"
        )
        for p in result.skipped:
            console.print(f"  [dim]·[/dim] {p.relative_to(plan.repo_root)}")
    if result.drifted:
        console.print(
            f"[red]{len(result.drifted)} file(s) drifted from manifest "
            f"(hand-edited)[/red]; use --force to overwrite"
        )
        for drift_path in result.drifted:
            console.print(f"  [dim]·[/dim] {drift_path}")

    if not result.dry_run:
        console.print(
            "\n[dim]Next:[/dim] commit `.harness/`, `AGENTS.md`, `SOUL.md`, `TOOLS.md`, "
            "`MEMORY.md`, `harness.config.json`, and `SKILLS/`. Your coding agent will "
            "pick them up automatically."
        )
