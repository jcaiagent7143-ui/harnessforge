"""check_idempotent — final step is marked idempotent (safe to retry)."""

from __future__ import annotations

import json
import os
from pathlib import Path


def run(target: Path) -> list[str]:
    out = os.environ.get("WORKFLOW_OUT")
    if out:
        path = Path(out)
    else:
        candidates = list(Path("/tmp").glob("*-workflow-output.json"))
        if not candidates:
            return ["SKIPPED: no agent output found"]
        path = candidates[0]

    if not path.exists():
        return [f"SKIPPED: {path} does not exist"]

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path} is not valid JSON: {e}"]

    plan = payload.get("plan", [])
    failures: list[str] = []

    if not isinstance(plan, list) or not plan:
        return ["plan is empty — cannot verify idempotency"]

    final = plan[-1]
    if not isinstance(final, dict):
        return ["final plan entry is not an object"]

    if not final.get("idempotent"):
        failures.append(
            f"final step {final.get('name')!r} is not marked idempotent — "
            "the workflow is unsafe to retry"
        )

    return failures
