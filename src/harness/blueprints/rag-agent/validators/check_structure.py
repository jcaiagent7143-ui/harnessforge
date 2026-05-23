"""check_structure — verify every blueprint-generated file is present and parses.

Run inside the aegis sandbox via ``aegis.synthesize.sandbox.load_harness``.
"""

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

EXPECTED_SKILLS = [
    "chunk-and-embed",
    "retrieve-and-rerank",
    "answer-with-citations",
    "eval-recall-precision",
]


def run(target: Path) -> list[str]:
    """Return a list of failure messages. Empty = pass."""
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
            if data.get("blueprint") != "rag-agent":
                failures.append(
                    f"harness.config.json blueprint is {data.get('blueprint')!r}, expected 'rag-agent'"
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
