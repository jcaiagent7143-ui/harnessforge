"""`harness version` — print the installed version."""

from __future__ import annotations

from rich.console import Console

import harness

console = Console()


def run() -> None:
    """Print the installed harness version."""
    console.print(f"harness-kit {harness.__version__}")
