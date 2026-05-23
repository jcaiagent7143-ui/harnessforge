"""check_tests — run the project's declared test_command and report.

Reads ``.harness/profile.yaml`` to find ``test_command``, then runs it.
Skips cleanly if no test_command is declared (the agent can elicit one).
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path


def run(target: Path) -> list[str]:
    profile_path = target / ".harness" / "profile.yaml"
    if not profile_path.exists():
        return ["SKIPPED: no .harness/profile.yaml"]

    # Lazy-read profile without importing yaml (validators must be small)
    test_command: str | None = None
    for line in profile_path.read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("test_command:"):
            value = stripped.split(":", 1)[1].strip()
            # Handle 'null', '~', '', or a quoted/unquoted string
            test_command = None if value in {"null", "~", ""} else value.strip("'").strip('"')
            break

    if not test_command:
        return ["SKIPPED: profile has no test_command (set it to enable this check)"]

    try:
        result = subprocess.run(
            shlex.split(test_command),
            cwd=target,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError as e:
        return [f"test_command not runnable: {e}"]
    except subprocess.TimeoutExpired:
        return [f"test_command timed out after 300s: {test_command!r}"]

    if result.returncode != 0:
        # Trim long stderr; keep the tail (where the failure usually surfaces)
        tail = (result.stderr or result.stdout)[-1200:]
        return [
            f"test_command exited {result.returncode}: {test_command!r}",
            f"output tail:\n{tail}",
        ]
    return []
