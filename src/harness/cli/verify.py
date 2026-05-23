"""`harness verify` — run the blueprint's validators against the current repo.

Exit codes:
  0 — all checks passed
  1 — one or more validators reported failures
  2 — configuration error (no blueprint, malformed config, etc.)
  3 — no harness.config.json (this isn't a harness-bootstrapped repo)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table

from harness.config import CONFIG_FILENAME, HarnessConfig

console = Console()


def run(
    target: Path = typer.Argument(Path("."), help="Repo to verify. Defaults to CWD."),
    check: str | None = typer.Option(
        None,
        "--check",
        "-c",
        help="Run only the named check (e.g. schema, citations, tests, lint).",
    ),
    tests_only: bool = typer.Option(
        False,
        "--tests",
        help="Shorthand for --check tests. Runs the project's declared test_command.",
    ),
    lint_only: bool = typer.Option(
        False,
        "--lint",
        help="Shorthand for --check lint. Runs the project's declared lint_command.",
    ),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Emit the stable JSON contract instead of a Rich table. "
        "Use this in CI or when an LLM is reading the output.",
    ),
    fail_fast: bool = typer.Option(
        False,
        "--fail-fast",
        help="Stop at the first failing check.",
    ),
) -> None:
    """Run blueprint validators; print JSON or a Rich summary."""
    root = target.resolve()
    cfg_path = root / CONFIG_FILENAME
    if not cfg_path.exists():
        console.print(
            f"[red]No {CONFIG_FILENAME} found. "
            f"This repo wasn't bootstrapped by harness — run `harness init` first.[/red]"
        )
        raise typer.Exit(code=3)

    try:
        cfg = HarnessConfig.load(cfg_path)
    except Exception as e:
        console.print(f"[red]Malformed {CONFIG_FILENAME}: {e}[/red]")
        raise typer.Exit(code=2) from e

    # Shorthand flags collapse to --check
    if tests_only and lint_only:
        console.print("[red]--tests and --lint are mutually exclusive[/red]")
        raise typer.Exit(code=2)
    if tests_only:
        check = "tests"
    elif lint_only:
        check = "lint"

    from harness.blueprints import load_blueprint
    from harness.validators import run_checks

    try:
        bp = load_blueprint(cfg.blueprint)
    except KeyError as e:
        console.print(f"[red]Blueprint {cfg.blueprint!r} not installed: {e}[/red]")
        raise typer.Exit(code=2) from e

    # Honest error if the user requested a check the blueprint doesn't define.
    if check is not None:
        defined = {v["name"] for v in bp.validators}
        if check not in defined:
            console.print(
                f"[yellow]Blueprint {cfg.blueprint!r} has no `{check}` validator. "
                f"Available: {sorted(defined)}[/yellow]"
            )
            raise typer.Exit(code=2)

    report = run_checks(bp, root, only=check, fail_fast=fail_fast)

    if output_json:
        print(json.dumps(report, indent=2, default=str))
    else:
        _render_table(report)

    if report["summary"]["failed"] > 0:
        raise typer.Exit(code=1)


def _render_table(report: dict[str, Any]) -> None:
    summary: dict[str, int] = report["summary"]
    checks: list[dict[str, Any]] = report["checks"]

    t = Table(title=f"harness verify · {report['blueprint']}")
    t.add_column("check", style="cyan")
    t.add_column("status")
    t.add_column("ms", justify="right", style="dim")
    t.add_column("messages")
    for c in checks:
        status = {
            "pass": "[green]pass[/green]",
            "fail": "[red]fail[/red]",
            "error": "[red on white]error[/red on white]",
            "skipped": "[dim]skipped[/dim]",
        }.get(c["status"], c["status"])
        t.add_row(
            c["name"],
            status,
            str(c["duration_ms"]),
            "\n".join(c["messages"]) if c["messages"] else "—",
        )
    console.print(t)

    color = "green" if summary["failed"] == 0 else "red"
    console.print(f"[{color}]{summary['passed']}/{summary['total']} passed[/{color}]")
