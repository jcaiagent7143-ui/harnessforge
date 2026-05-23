"""`harness sync` — re-render adapters + blueprint files from an existing profile.

With ``--check``, exits non-zero if any generated file has been hand-edited
since the last write. Designed for CI: drop into a GitHub Action to keep
the generated layer in sync with the profile.
"""

from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from harness.config import CONFIG_FILENAME, HarnessConfig
from harness.manifest import MANIFEST_FILENAME, Manifest, detect_drift
from harness.provision import provision_sync

console = Console()


def run(
    path: Path = typer.Argument(Path("."), help="Repo to sync. Defaults to CWD."),
    adapters: str | None = typer.Option(
        None,
        "--adapter",
        help="Comma-separated IDE adapters to re-render. Default: all configured.",
    ),
    check: bool = typer.Option(
        False,
        "--check",
        help="Exit non-zero if any generated file has drifted. Writes nothing.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite drifted files (only meaningful without --check).",
    ),
) -> None:
    """Re-render IDE adapters + blueprint files from the existing profile."""
    root = path.resolve()
    cfg_path = root / CONFIG_FILENAME
    manifest_path = root / MANIFEST_FILENAME

    if not cfg_path.exists():
        console.print(f"[red]No {CONFIG_FILENAME} found at {root}.[/red] Run `harness init` first.")
        raise typer.Exit(code=2)

    if check:
        if not manifest_path.exists():
            console.print(f"[yellow]No {MANIFEST_FILENAME} found — cannot detect drift.[/yellow]")
            raise typer.Exit(code=2)
        manifest = Manifest.load(manifest_path)
        drifted = detect_drift(root, manifest)
        if drifted:
            console.print(f"[red]{len(drifted)} file(s) drifted:[/red]")
            for e in drifted:
                console.print(f"  · {e.path}")
            raise typer.Exit(code=1)
        console.print(f"[green]✓ no drift — {len(manifest.entries)} files in sync[/green]")
        return

    cfg = HarnessConfig.load(cfg_path)
    adapter_list = [a.strip() for a in adapters.split(",")] if adapters else None

    with console.status("[bold cyan]re-rendering...", spinner="dots"):
        result = provision_sync(
            root,
            blueprint=cfg.blueprint,
            no_llm=True,  # sync uses the existing profile — no LLM needed
            force=force,
            adapters=adapter_list,
        )

    console.print(f"[green]✓ wrote {len(result.written)} files[/green]")
    if result.skipped:
        console.print(
            f"[yellow]skipped {len(result.skipped)} files[/yellow] (use --force to overwrite)"
        )
