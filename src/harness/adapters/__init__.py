"""IDE adapters — render a HarnessProfile into each IDE's native config.

This is the "works in every IDE" part of the value prop. Each adapter is
a tiny module that knows one tool's config format and writes the right
file(s) into the project root.

Add a new adapter:

  1. Write ``harness/adapters/<tool>.py`` exporting ``render(profile, root)``
  2. Register it in ``ALL_ADAPTERS`` below
  3. ``harness sync`` will run it automatically next time.
"""

from __future__ import annotations

from pathlib import Path

from harness.adapters import claude, codex, continue_, cursor, windsurf
from harness.profile import HarnessProfile

# (name, render_callable, output_paths) tuples
ALL_ADAPTERS = [
    ("claude-code", claude.render, claude.OUTPUTS),
    ("cursor", cursor.render, cursor.OUTPUTS),
    ("continue", continue_.render, continue_.OUTPUTS),
    ("codex-cli", codex.render, codex.OUTPUTS),
    ("windsurf", windsurf.render, windsurf.OUTPUTS),
]


def render_all(profile: HarnessProfile, root: Path) -> dict[str, list[Path]]:
    """Run every adapter; return a name → written-files map."""
    written: dict[str, list[Path]] = {}
    for name, fn, _ in ALL_ADAPTERS:
        try:
            paths = fn(profile, root)
            written[name] = paths
        except Exception as e:  # adapter failures should never break init
            written[name] = []
            print(f"[harness] WARNING: adapter {name!r} failed: {e}")
    return written


__all__ = ["ALL_ADAPTERS", "render_all"]
