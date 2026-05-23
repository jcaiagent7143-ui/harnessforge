"""check_lint — run the project's declared lint_command and report."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path


def run(target: Path) -> list[str]:
    profile_path = target / ".harness" / "profile.yaml"
    if not profile_path.exists():
        return ["SKIPPED: no .harness/profile.yaml"]

    lint_command: str | None = None
    for line in profile_path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("lint_command:"):
            value = stripped.split(":", 1)[1].strip()
            lint_command = None if value in {"null", "~", ""} else value.strip("'").strip('"')
            break

    if not lint_command:
        return ["SKIPPED: profile has no lint_command"]

    try:
        result = subprocess.run(
            shlex.split(lint_command),
            cwd=target,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except FileNotFoundError as e:
        return [f"lint_command not runnable: {e}"]
    except subprocess.TimeoutExpired:
        return [f"lint_command timed out after 120s: {lint_command!r}"]

    if result.returncode != 0:
        tail = (result.stderr or result.stdout)[-800:]
        return [f"lint_command exited {result.returncode}: {lint_command!r}", f"output:\n{tail}"]
    return []
