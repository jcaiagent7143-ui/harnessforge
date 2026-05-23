"""check_tool_log — every tool call in the agent output has a log entry."""

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
    tool_log = payload.get("tool_log", [])
    failures: list[str] = []

    plan_steps_with_tools = [s for s in plan if isinstance(s, dict) and s.get("tool")]
    logged_steps = {e.get("step") for e in tool_log if isinstance(e, dict)}

    for s in plan_steps_with_tools:
        step_id = s.get("step")
        if step_id not in logged_steps:
            failures.append(
                f"plan step {step_id} ({s.get('name')!r}) used a tool but has no tool_log entry"
            )

    for i, e in enumerate(tool_log):
        if not isinstance(e, dict):
            continue
        for k in ("tool", "args", "ok", "started_at"):
            if k not in e:
                failures.append(f"tool_log[{i}] missing {k!r}")

    return failures
