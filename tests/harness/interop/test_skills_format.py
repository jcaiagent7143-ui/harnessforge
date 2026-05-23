"""Interop tests — generated SKILL.md files must be readable by any
tool that follows the ``anthropics/skills`` convention.

We don't depend on Anthropic's repo directly; we test the structural
contract: YAML frontmatter with required keys, a non-empty markdown body,
kebab-case names, and parsability with PyYAML.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from harness.blueprints import iter_catalog_skills, load_blueprint
from harness.provision import provision_sync
from harness.skills_io import Skill, list_skills, validate_skill

# ── catalog skills ────────────────────────────────────────────────────────


def test_every_catalog_skill_is_valid() -> None:
    """Every SKILL.md we ship must pass `validate_skill`."""
    catalog = list(iter_catalog_skills())
    assert catalog
    issues_by_skill: dict[str, list[str]] = {}
    for bp_name, skill in catalog:
        issues = validate_skill(skill)
        if issues:
            issues_by_skill[f"{bp_name}/{skill.name}"] = issues
    assert not issues_by_skill, f"invalid skills: {issues_by_skill}"


def test_every_catalog_skill_parses_yaml_frontmatter() -> None:
    from harness.skills_io import FRONTMATTER_RE

    catalog = list(iter_catalog_skills())
    for bp_name, skill in catalog:
        text = skill.to_markdown()
        assert text.startswith("---\n"), f"{bp_name}/{skill.name}: missing frontmatter delim"
        m = FRONTMATTER_RE.match(text)
        assert m, f"{bp_name}/{skill.name}: frontmatter regex did not match"
        front_text, body = m.group(1), m.group(2)
        parsed = yaml.safe_load(front_text)
        assert isinstance(parsed, dict)
        assert parsed.get("name") == skill.name
        assert parsed.get("description")
        assert body.strip()


def test_every_catalog_skill_has_required_keys() -> None:
    """Anthropics/skills requires at minimum: name, description, body."""
    catalog = list(iter_catalog_skills())
    for bp_name, skill in catalog:
        assert skill.name, f"{bp_name}: empty name"
        assert skill.description, f"{bp_name}/{skill.name}: empty description"
        assert skill.body.strip(), f"{bp_name}/{skill.name}: empty body"


# ── rendered skills (in a bootstrapped repo) ──────────────────────────────


@pytest.mark.parametrize(
    "blueprint",
    ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"],
)
def test_rendered_skills_pass_validate_skill(tmp_repo: Path, blueprint: str) -> None:
    """After `harness init`, every SKILL.md under SKILLS/ must validate."""
    provision_sync(tmp_repo, blueprint=blueprint, no_llm=True)
    skills = list_skills(tmp_repo / "SKILLS")
    assert skills, f"{blueprint} rendered no skills"
    for skill in skills:
        issues = validate_skill(skill)
        assert not issues, f"rendered skill {skill.name!r} invalid: {issues}"


@pytest.mark.parametrize(
    "blueprint",
    ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"],
)
def test_rendered_skills_reparse_from_disk(tmp_repo: Path, blueprint: str) -> None:
    """Roundtrip: write a skill, read it back, names + descriptions match."""
    provision_sync(tmp_repo, blueprint=blueprint, no_llm=True)
    for skill_dir in (tmp_repo / "SKILLS").iterdir():
        md = skill_dir / "SKILL.md"
        if not md.exists():
            continue
        skill = Skill.parse(md.read_text(), name_hint=skill_dir.name)
        assert skill.name == skill_dir.name
        assert skill.description
        assert skill.body.strip()


# ── the universal AGENTS.md convention ────────────────────────────────────


@pytest.mark.parametrize(
    "blueprint",
    ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"],
)
def test_AGENTS_md_is_present_and_nonempty(tmp_repo: Path, blueprint: str) -> None:
    """AGENTS.md is the universal entry point — every coding agent reads it."""
    provision_sync(tmp_repo, blueprint=blueprint, no_llm=True)
    agents_md = tmp_repo / "AGENTS.md"
    assert agents_md.exists()
    text = agents_md.read_text()
    assert len(text) > 200, "AGENTS.md is suspiciously short"
    assert "harness" in text.lower()


# ── memory schemas are valid JSON Schema ──────────────────────────────────


@pytest.mark.parametrize(
    "blueprint",
    ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"],
)
def test_memory_schemas_are_valid_jsonschema(blueprint: str) -> None:
    """Every memory schema must parse as a JSON object with a $schema key."""
    import json

    # Touch the blueprint to ensure it loads (validates blueprint.yaml shape too)
    _bp = load_blueprint(blueprint)
    assert _bp.name == blueprint
    from harness.blueprints import blueprint_dir

    schemas_dir = blueprint_dir(blueprint) / "memory_schemas"
    if not schemas_dir.is_dir():
        pytest.skip(f"{blueprint} has no memory_schemas/")
    for schema_file in schemas_dir.glob("*.json"):
        data = json.loads(schema_file.read_text())
        assert "$schema" in data, f"{schema_file.name} missing $schema"
        assert data.get("type"), f"{schema_file.name} missing type"
