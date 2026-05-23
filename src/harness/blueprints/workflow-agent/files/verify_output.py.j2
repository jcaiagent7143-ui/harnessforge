"""verify_output.py — confirm a workflow run logged every step + marked the
final step idempotent."""
from __future__ import annotations

import json
from typing import Any


def verify(payload_json: str | dict[str, Any]) -> list[str]:
    failures: list[str] = []
    try:
        payload = payload_json if isinstance(payload_json, dict) else json.loads(payload_json)
    except (json.JSONDecodeError, TypeError) as e:
        return [f"output not valid JSON: {e}"]

    if not isinstance(payload, dict):
        return [f"output must be an object, got {type(payload).__name__}"]

    plan = payload.get("plan", [])
    tool_log = payload.get("tool_log", [])
    if not isinstance(plan, list) or not plan:
        failures.append("plan must be a non-empty list of steps")
    if not isinstance(tool_log, list):
        failures.append("tool_log must be a list (possibly empty if no tools used)")

    # Each tool_log entry needs: tool, args, ok, started_at
    for i, entry in enumerate(tool_log):
        if not isinstance(entry, dict):
            failures.append(f"tool_log[{i}] must be object")
            continue
        for k in ("tool", "args", "ok", "started_at"):
            if k not in entry:
                failures.append(f"tool_log[{i}] missing {k!r}")

    if payload.get("final_status") not in {"ok", "failed", "partial"}:
        failures.append("final_status must be ok|failed|partial")

    if payload.get("final_status") == "ok" and not payload.get("idempotent_marker"):
        failures.append("final_status=ok requires idempotent_marker (safe-to-retry attestation)")

    return failures
