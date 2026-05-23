"""check_ticket_lineage — every ticket must link to a conversation turn."""

from __future__ import annotations

import json
import os
from pathlib import Path


def run(target: Path) -> list[str]:
    out = os.environ.get("SUPPORT_OUT")
    if out:
        path = Path(out)
    else:
        candidates = list(Path("/tmp").glob("*-support-output.json"))
        if not candidates:
            return ["SKIPPED: no agent output found at $SUPPORT_OUT or /tmp/*-support-output.json"]
        path = candidates[0]

    if not path.exists():
        return [f"SKIPPED: {path} does not exist"]

    try:
        payload = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        return [f"{path} is not valid JSON: {e}"]

    if payload.get("action") not in {"ticketed", "escalated"}:
        return []  # nothing to lineage-check

    ticket = payload.get("ticket")
    if not isinstance(ticket, dict):
        return ["action is ticketed/escalated but 'ticket' object is missing"]

    failures: list[str] = []
    if not ticket.get("conversation_id"):
        failures.append("ticket missing conversation_id (orphan ticket)")
    lineage = payload.get("lineage")
    if not isinstance(lineage, list) or not lineage:
        failures.append("ticket missing top-level 'lineage' (turn references)")
    else:
        for i, entry in enumerate(lineage):
            if not isinstance(entry, dict):
                failures.append(f"lineage[{i}] must be object")
                continue
            if "turn" not in entry:
                failures.append(f"lineage[{i}] missing 'turn'")
            if "message_id" not in entry:
                failures.append(f"lineage[{i}] missing 'message_id'")

    return failures
