"""check_sla — every ticket priority must be in the documented SLA matrix."""

from __future__ import annotations

import json
import os
from pathlib import Path

VALID_PRIORITIES = {"P0", "P1", "P2", "P3"}


def run(target: Path) -> list[str]:
    out = os.environ.get("SUPPORT_OUT")
    if out:
        path = Path(out)
    else:
        candidates = list(Path("/tmp").glob("*-support-output.json"))
        if not candidates:
            return ["SKIPPED: no agent output found"]
        path = candidates[0]

    if not path.exists():
        return [f"SKIPPED: {path} does not exist"]

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path} is not valid JSON: {e}"]

    ticket = payload.get("ticket")
    if not isinstance(ticket, dict):
        return []  # nothing to check

    failures: list[str] = []
    pri = ticket.get("priority")
    if pri not in VALID_PRIORITIES:
        failures.append(f"ticket.priority {pri!r} is not in {sorted(VALID_PRIORITIES)}")
    if not ticket.get("sla_due_at"):
        failures.append("ticket missing sla_due_at — derive from priority + now()")

    return failures
