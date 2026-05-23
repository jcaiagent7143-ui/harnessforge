"""`harness doctor` — diagnose the local environment.

Checks:
  * which LLM provider extras are installed
  * which provider API keys are set
  * whether the current dir looks like a bootstrapped harness repo
  * whether ``harness verify`` would have anything to do here
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

import harness
from harness.config import CONFIG_FILENAME

console = Console()


PROVIDERS = [
    ("anthropic", "ANTHROPIC_API_KEY"),
    ("openai", "OPENAI_API_KEY"),
    ("google.genai", "GOOGLE_API_KEY"),
    ("ollama", None),
    ("litellm", None),
]


def run(
    path: Path = typer.Argument(Path("."), help="Repo to diagnose. Defaults to CWD."),
) -> None:
    """Print a diagnostic report for the current shell + repo."""
    console.rule(f"[bold]harness doctor[/bold] · harnessforge {harness.__version__}")

    # Providers
    t = Table(title="LLM providers")
    t.add_column("provider")
    t.add_column("extra installed?")
    t.add_column("API key set?")
    for mod, env in PROVIDERS:
        # find_spec() raises ModuleNotFoundError when an ancestor package
        # ("google" for "google.genai") is missing — guard explicitly.
        try:
            installed = "[green]yes[/green]" if importlib.util.find_spec(mod) else "[dim]no[/dim]"
        except (ModuleNotFoundError, ValueError):
            installed = "[dim]no[/dim]"
        if env is None:
            key = "[dim]n/a[/dim]"
        else:
            key = "[green]yes[/green]" if os.environ.get(env) else "[dim]no[/dim]"
        t.add_row(mod.split(".")[0], installed, key)
    console.print(t)

    # Repo state
    root = path.resolve()
    config_present = (root / CONFIG_FILENAME).exists()
    profile_present = (root / ".harness" / "profile.yaml").exists()
    manifest_present = (root / ".harness" / "manifest.json").exists()
    skills_present = (root / "SKILLS").is_dir()

    t2 = Table(title=f"repo: {root}")
    t2.add_column("artifact")
    t2.add_column("present?")
    t2.add_row(CONFIG_FILENAME, _yn(config_present))
    t2.add_row(".harness/profile.yaml", _yn(profile_present))
    t2.add_row(".harness/manifest.json", _yn(manifest_present))
    t2.add_row("SKILLS/", _yn(skills_present))
    for adapter in ("AGENTS.md", "SOUL.md", "TOOLS.md", "MEMORY.md"):
        t2.add_row(adapter, _yn((root / adapter).exists()))
    for ide in (".claude/CLAUDE.md", ".cursor/rules", ".continue/config.json", ".windsurf/rules"):
        t2.add_row(ide, _yn((root / ide).exists()))
    console.print(t2)

    if not config_present:
        console.print(
            "[yellow]Tip:[/yellow] this repo has no `harness.config.json`. "
            "Run `harness init` to bootstrap."
        )


def _yn(b: bool) -> str:
    return "[green]✓[/green]" if b else "[dim]·[/dim]"
