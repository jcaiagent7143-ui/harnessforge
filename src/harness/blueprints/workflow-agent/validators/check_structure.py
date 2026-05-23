"""check_structure — every blueprint-generated file present and parses."""

from __future__ import annotations

import json
from pathlib import Path

EXPECTED_FILES = [
    "AGENTS.md",
    "SOUL.md",
    "TOOLS.md",
    "MEMORY.md",
    "harness.config.json",
    ".harness/profile.yaml",
    "scripts/test_task.sh",
    "scripts/verify_output.py",
]

EXPECTED_SKILLS = ["decompose-task", "call-tool-with-retry", "check-result"]


def run(target: Path) -> list[str]:
    failures: list[str] = []
    for rel in EXPECTED_FILES:
        p = target / rel
        if not p.exists():
            failures.append(f"missing: {rel}")
            continue
        if p.stat().st_size == 0:
            failures.append(f"empty: {rel}")

    cfg = target / "harness.config.json"
    if cfg.exists():
        try:
            data = json.loads(cfg.read_text())
            if data.get("blueprint") != "workflow-agent":
                failures.append(
                    f"harness.config.json blueprint is {data.get('blueprint')!r}, expected 'workflow-agent'"
                )
        except json.JSONDecodeError as e:
            failures.append(f"harness.config.json is not valid JSON: {e}")

    skills_dir = target / "SKILLS"
    if not skills_dir.is_dir():
        failures.append("missing: SKILLS/ directory")
    else:
        for skill in EXPECTED_SKILLS:
            sk = skills_dir / skill / "SKILL.md"
            if not sk.exists():
                failures.append(f"missing: SKILLS/{skill}/SKILL.md")

    return failures
