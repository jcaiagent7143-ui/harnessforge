"""Unit tests for skills_io — anthropics/skills compatibility."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.skills_io import Skill, list_skills, load_skill, validate_skill, write_skill

SAMPLE_SKILL = """---
name: my-skill
description: Does a thing that needs doing.
version: 1.0.0
when_to_use: When the thing needs doing.
inputs:
  - {name: in1, type: string, required: true}
outputs:
  - {name: out1, type: object}
---

# My Skill

## Steps
1. Do the thing.
2. Confirm it's done.
"""


def test_parse_skill_with_frontmatter() -> None:
    skill = Skill.parse(SAMPLE_SKILL)
    assert skill.name == "my-skill"
    assert skill.description.startswith("Does a thing")
    assert skill.version == "1.0.0"
    assert skill.when_to_use
    assert skill.inputs == [{"name": "in1", "type": "string", "required": True}]
    assert skill.outputs == [{"name": "out1", "type": "object"}]
    assert "My Skill" in skill.body


def test_parse_skill_body_only_synthesizes_metadata() -> None:
    skill = Skill.parse("# Thing\n\nDoes a thing.\n", name_hint="thing-skill")
    assert skill.name == "thing-skill"
    assert skill.description  # nonempty


def test_to_markdown_roundtrip() -> None:
    original = Skill.parse(SAMPLE_SKILL)
    rendered = original.to_markdown()
    reparsed = Skill.parse(rendered)
    assert reparsed.name == original.name
    assert reparsed.description == original.description
    assert reparsed.version == original.version
    assert reparsed.body.strip() == original.body.strip()


def test_write_and_load_skill_roundtrip(tmp_path: Path) -> None:
    skill = Skill.parse(SAMPLE_SKILL)
    write_skill(skill, tmp_path)
    loaded = load_skill(tmp_path)
    assert loaded.name == "my-skill"
    assert loaded.description == skill.description


def test_list_skills_finds_all(tmp_path: Path) -> None:
    for name in ("alpha-skill", "beta-skill", "gamma-skill"):
        skill_dir = tmp_path / name
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            SAMPLE_SKILL.replace("my-skill", name)
        )
    skills = list_skills(tmp_path)
    assert sorted(s.name for s in skills) == ["alpha-skill", "beta-skill", "gamma-skill"]


def test_validate_skill_rejects_bad_name() -> None:
    skill = Skill(name="BadName", description="A perfectly fine description here.")
    issues = validate_skill(skill)
    assert any("kebab-case" in i for i in issues)


def test_validate_skill_rejects_short_description() -> None:
    skill = Skill(name="good-name", description="short")
    issues = validate_skill(skill)
    assert any("10 characters" in i for i in issues)


def test_validate_skill_accepts_well_formed() -> None:
    skill = Skill.parse(SAMPLE_SKILL)
    assert validate_skill(skill) == []


def test_truly_invalid_yaml_frontmatter_raises() -> None:
    # A YAML parse error (unterminated quote) — must surface as ValueError.
    bad = '---\nname: "unterminated\n---\n\nbody'
    with pytest.raises(ValueError, match="not valid YAML"):
        Skill.parse(bad)


def test_non_mapping_frontmatter_raises() -> None:
    # A YAML list (not a mapping) — surfaces as a different ValueError.
    bad = "---\n- one\n- two\n---\n\nbody"
    with pytest.raises(ValueError, match="must be a mapping"):
        Skill.parse(bad)
