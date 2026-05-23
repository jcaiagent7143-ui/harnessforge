"""Continue.dev adapter — renders .continue/config.json fragments.

Continue uses ``~/.continue/config.json`` globally; for per-repo behavior
it picks up ``.continue/config.json``. We write a per-repo override that
sets ``systemMessage`` to the harness profile summary and lists the
project's recommended MCP servers.
"""

from __future__ import annotations

import json
from pathlib import Path

from harness.profile import HarnessProfile

OUTPUTS = [".continue/config.json"]


def render(profile: HarnessProfile, root: Path) -> list[Path]:
    out_dir = root / ".continue"
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "config.json"
    target.write_text(json.dumps(_compose(profile), indent=2))
    return [target]


def _compose(p: HarnessProfile) -> dict[str, object]:
    cmds = []
    if p.test_command:
        cmds.append(f"Tests: {p.test_command}")
    if p.lint_command:
        cmds.append(f"Lint: {p.lint_command}")
    if p.build_command:
        cmds.append(f"Build: {p.build_command}")

    system = (
        f"You are working in {p.name}, a {p.project_type} written in {p.primary_language}. "
        f"Frameworks: {', '.join(p.frameworks) or 'none'}. "
        f"{p.description}\n\n"
        f"Conventions: {' | '.join(p.conventions)}\n\n"
        f"Commands: {' | '.join(cmds)}\n\n"
        f"Forbidden paths: {', '.join(p.forbidden_paths)}\n"
        f"Forbidden commands: {', '.join(p.forbidden_commands)}\n"
        f"Always ask before: {' | '.join(p.requires_human_approval)}\n\n"
        f"Definition of done: {' | '.join(p.success_criteria)}"
    )

    return {
        "_generatedBy": f"harness v{p.harness_version}",
        "_source": ".harness/profile.yaml",
        "systemMessage": system,
        "experimental": {
            "modelContextProtocolServers": [
                {"transport": "stdio", "name": m} for m in p.recommended_mcps
            ],
        },
    }
