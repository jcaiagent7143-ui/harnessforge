"""`harness skills` — list / show / add anthropics/skills-compatible skills."""

from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from harness.skills_io import Skill, list_skills, load_skill

app = typer.Typer(help="Manage anthropics/skills-compatible skills.", no_args_is_help=True)
console = Console()


@app.command("list")
def list_cmd(
    path: Path = typer.Argument(Path("."), help="Repo to scan. Defaults to CWD."),
) -> None:
    """List skills under ./SKILLS/ and the blueprint catalog."""
    skills_dir = path / "SKILLS"
    local = list_skills(skills_dir)

    if local:
        t = Table(title=f"Local SKILLS/ ({len(local)})")
        t.add_column("name", style="cyan")
        t.add_column("version", style="dim")
        t.add_column("description")
        for s in local:
            t.add_row(s.name, s.version, s.description[:80])
        console.print(t)
    else:
        console.print("[dim]No local SKILLS/ directory.[/dim]")

    # Catalog (blueprint-provided skills)
    catalog = _catalog_skills()
    if catalog:
        t = Table(title=f"Available from blueprints ({len(catalog)})")
        t.add_column("blueprint", style="dim")
        t.add_column("skill", style="cyan")
        t.add_column("description")
        for bp_name, skill in catalog:
            t.add_row(bp_name, skill.name, skill.description[:80])
        console.print(t)


@app.command("show")
def show_cmd(
    name: str = typer.Argument(..., help="Skill name to print."),
    path: Path = typer.Argument(Path("."), help="Repo to scan. Defaults to CWD."),
) -> None:
    """Print a skill's SKILL.md."""
    skill_dir = path / "SKILLS" / name
    if skill_dir.is_dir():
        skill = load_skill(skill_dir)
        console.print(Panel(skill.to_markdown(), title=f"{skill.name} v{skill.version}"))
        return

    # Try catalog
    for bp_name, skill in _catalog_skills():
        if skill.name == name:
            console.print(
                Panel(skill.to_markdown(), title=f"{skill.name} v{skill.version} ({bp_name})")
            )
            return

    console.print(f"[red]Skill {name!r} not found.[/red]")
    raise typer.Exit(code=2)


@app.command("add")
def add_cmd(
    name: str = typer.Argument(..., help="Skill name from the blueprint catalog OR new name for --domain."),
    path: Path = typer.Argument(Path("."), help="Repo to add into. Defaults to CWD."),
    domain: bool = typer.Option(
        False,
        "--domain",
        help="Create a starter domain skill under SKILLS/domain/<name>/ instead of copying from catalog. "
        "Use this for project-specific procedures that don't belong in any shipped blueprint "
        "(e.g. 'fetch-prices', 'compute-portfolio-pnl', 'send-trade-confirmation').",
    ),
    description: str | None = typer.Option(
        None,
        "--description",
        "-d",
        help="One-line description (≥10 chars) for the new domain skill. Required with --domain.",
    ),
) -> None:
    """Copy a blueprint-provided skill into local SKILLS/, OR create a new domain skill."""
    if domain:
        _add_domain_skill(name=name, path=path, description=description)
        return

    for bp_name, skill in _catalog_skills():
        if skill.name == name:
            from harness.blueprints import blueprint_skill_source_dir, load_blueprint

            bp = load_blueprint(bp_name)
            src = blueprint_skill_source_dir(bp, name)
            dst = path / "SKILLS" / name
            if dst.exists():
                console.print(f"[yellow]{dst} already exists — refusing to overwrite[/yellow]")
                raise typer.Exit(code=1)
            shutil.copytree(src, dst)
            console.print(f"[green]✓ added skill {name!r} from {bp_name}[/green]")
            return

    console.print(
        f"[red]Skill {name!r} not found in any blueprint.[/red] "
        f"To create a new project-specific skill, re-run with [cyan]--domain[/cyan]."
    )
    raise typer.Exit(code=2)


def _add_domain_skill(*, name: str, path: Path, description: str | None) -> None:
    """Create a starter SKILL.md under SKILLS/domain/<name>/ for a project-specific procedure."""
    import re

    from harness.skills_io import Skill, write_skill

    if not re.match(r"^[a-z][a-z0-9-]*$", name):
        console.print(
            f"[red]Skill name {name!r} must be kebab-case "
            "(lowercase letters, digits, hyphens; starts with a letter).[/red]"
        )
        raise typer.Exit(code=2)
    if not description or len(description) < 10:
        console.print(
            "[red]--description is required (≥10 chars) when using --domain. "
            "It's what the agent reads to decide whether to invoke this skill.[/red]"
        )
        raise typer.Exit(code=2)

    dst = path / "SKILLS" / "domain" / name
    if dst.exists():
        console.print(f"[yellow]{dst} already exists — refusing to overwrite[/yellow]")
        raise typer.Exit(code=1)

    body = (
        f"# {name.replace('-', ' ').title()}\n\n"
        "## Steps\n\n"
        "1. _Fill in the concrete steps the agent should follow._\n"
        "2. _Reference the project files / commands / APIs by exact name._\n"
        "3. _Be specific about inputs, outputs, and where data lives._\n\n"
        "## Failure modes to avoid\n\n"
        "- _List the predictable ways this can go wrong, with examples._\n"
    )
    skill = Skill(
        name=name,
        description=description,
        version="0.1.0",
        when_to_use="_Fill in: under what conditions should the agent reach for this skill?_",
        body=body,
    )
    write_skill(skill, dst)
    console.print(
        f"[green]✓ created domain skill at SKILLS/domain/{name}/SKILL.md[/green]\n"
        f"[dim]Edit it to describe the project-specific procedure. "
        f"Agents will discover it through `harness skills list`.[/dim]"
    )


# ── helpers ────────────────────────────────────────────────────────────────


def _catalog_skills() -> list[tuple[str, Skill]]:
    """Walk every blueprint and gather its skills."""
    try:
        from harness.blueprints import iter_catalog_skills

        return list(iter_catalog_skills())
    except ImportError:
        return []
