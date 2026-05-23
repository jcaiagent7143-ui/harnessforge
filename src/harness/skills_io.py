"""Skills I/O — read, write, and validate ``anthropics/skills``-compatible
SKILL.md files.

The format is a markdown file with YAML frontmatter::

    ---
    name: chunk-and-embed
    description: Split documents into chunks and embed them
    version: 1.0.0
    when_to_use: When you need to ingest documents for RAG
    inputs:
      - {name: docs_dir, type: path, required: true}
    outputs:
      - {name: chunks_index, type: path}
    ---

    # Chunk and Embed

    ## Steps
    1. ...

Any directory under a project's ``SKILLS/`` is one skill. The directory name
is the skill name (kebab-case). Optional resource files may sit alongside
``SKILL.md`` — we copy them verbatim during rendering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

SKILL_FILENAME = "SKILL.md"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)$", re.DOTALL)


@dataclass
class Skill:
    """A single anthropics/skills-compatible skill."""

    name: str
    description: str
    version: str = "1.0.0"
    when_to_use: str = ""
    body: str = ""
    inputs: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    resources: list[str] = field(default_factory=list)
    extras: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """Render back to SKILL.md format with YAML frontmatter."""
        front: dict[str, Any] = {
            "name": self.name,
            "description": self.description,
            "version": self.version,
        }
        if self.when_to_use:
            front["when_to_use"] = self.when_to_use
        if self.inputs:
            front["inputs"] = self.inputs
        if self.outputs:
            front["outputs"] = self.outputs
        front.update(self.extras)
        fm = yaml.safe_dump(front, sort_keys=False).strip()
        return f"---\n{fm}\n---\n\n{self.body.strip()}\n"

    @classmethod
    def parse(cls, text: str, *, name_hint: str | None = None) -> Skill:
        """Parse a SKILL.md text blob. Raises ValueError on malformed input."""
        m = FRONTMATTER_RE.match(text)
        if not m:
            # Allow body-only files — synthesize minimal metadata
            return cls(
                name=name_hint or "unnamed",
                description=_first_nonempty_line(text) or "(no description)",
                body=text.strip(),
            )
        front_text, body = m.group(1), m.group(2)
        try:
            front = yaml.safe_load(front_text) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"SKILL.md frontmatter is not valid YAML: {e}") from e
        if not isinstance(front, dict):
            raise ValueError(f"SKILL.md frontmatter must be a mapping, got {type(front).__name__}")
        name = front.pop("name", name_hint or "unnamed")
        description = front.pop("description", "")
        version = front.pop("version", "1.0.0")
        when_to_use = front.pop("when_to_use", "")
        inputs = front.pop("inputs", []) or []
        outputs = front.pop("outputs", []) or []
        return cls(
            name=str(name),
            description=str(description),
            version=str(version),
            when_to_use=str(when_to_use),
            body=body.strip(),
            inputs=list(inputs),
            outputs=list(outputs),
            extras=front,  # forward-compat: keep unknown keys
        )


# ── disk operations ────────────────────────────────────────────────────────


def load_skill(skill_dir: Path) -> Skill:
    """Load a single skill from a directory containing SKILL.md."""
    if not skill_dir.is_dir():
        raise ValueError(f"{skill_dir} is not a directory")
    md = skill_dir / SKILL_FILENAME
    if not md.exists():
        raise FileNotFoundError(f"{md} not found")
    skill = Skill.parse(md.read_text(), name_hint=skill_dir.name)
    skill.resources = sorted(
        str(p.relative_to(skill_dir))
        for p in skill_dir.rglob("*")
        if p.is_file() and p.name != SKILL_FILENAME
    )
    return skill


def write_skill(skill: Skill, skill_dir: Path) -> Path:
    """Write a single skill to disk. Creates the directory; returns SKILL.md path."""
    skill_dir.mkdir(parents=True, exist_ok=True)
    md = skill_dir / SKILL_FILENAME
    md.write_text(skill.to_markdown())
    return md


def list_skills(skills_root: Path) -> list[Skill]:
    """List every skill under a SKILLS/ directory (and SKILLS/domain/). Empty list if none.

    Recurses one level into subdirectories that don't themselves contain a
    SKILL.md — this is what makes ``SKILLS/domain/<name>/SKILL.md`` discoverable
    alongside top-level blueprint skills.
    """
    if not skills_root.is_dir():
        return []
    out: list[Skill] = []
    for child in sorted(skills_root.iterdir()):
        if not child.is_dir():
            continue
        if (child / SKILL_FILENAME).exists():
            try:
                out.append(load_skill(child))
            except (ValueError, FileNotFoundError):
                continue
        else:
            # Container directory (e.g. SKILLS/domain/) — recurse one level
            for grand in sorted(child.iterdir()):
                if grand.is_dir() and (grand / SKILL_FILENAME).exists():
                    try:
                        out.append(load_skill(grand))
                    except (ValueError, FileNotFoundError):
                        continue
    return out


def validate_skill(skill: Skill) -> list[str]:
    """Lightweight validation. Returns a list of human-readable issues.

    Empty list = valid. We deliberately do not validate against a strict
    JSON Schema to stay forward-compatible with anthropics/skills evolution.
    """
    issues: list[str] = []
    if not skill.name or not re.match(r"^[a-z][a-z0-9-]*$", skill.name):
        issues.append(f"name {skill.name!r} should be kebab-case (lower, hyphens, digits)")
    if not skill.description or len(skill.description) < 10:
        issues.append("description should be at least 10 characters")
    if len(skill.description) > 1024:
        issues.append("description should be under 1024 characters")
    if not skill.body.strip():
        issues.append("body is empty — a SKILL.md should describe what to do")
    return issues


def _first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        s = line.strip().lstrip("#").strip()
        if s:
            return s
    return ""


__all__ = [
    "SKILL_FILENAME",
    "Skill",
    "list_skills",
    "load_skill",
    "validate_skill",
    "write_skill",
]
