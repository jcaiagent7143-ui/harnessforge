"""v0.2 SKILLS/domain/ convention — project-specific skills authored by the user."""

from __future__ import annotations

from pathlib import Path

from harness.skills_io import Skill, list_skills, validate_skill, write_skill


def test_domain_skill_discovered_under_skills_domain(tmp_path: Path) -> None:
    """A skill at SKILLS/domain/<name>/SKILL.md should be found by list_skills."""
    domain_dir = tmp_path / "SKILLS" / "domain" / "fetch-prices"
    skill = Skill(
        name="fetch-prices",
        description="Fetch live equity prices from the configured data source.",
        version="0.1.0",
        body="# Fetch Prices\n\n## Steps\n1. Pick source.\n2. Call API.\n",
    )
    write_skill(skill, domain_dir)

    skills = list_skills(tmp_path / "SKILLS")
    names = {s.name for s in skills}
    assert "fetch-prices" in names


def test_domain_skill_coexists_with_blueprint_skills(tmp_path: Path) -> None:
    """SKILLS/<blueprint-skill>/ + SKILLS/domain/<custom>/ should both surface."""
    # Blueprint-shipped skill (top-level)
    write_skill(
        Skill(name="decompose-task", description="Plan generator described here.", body="# X\n## Steps\n1. y"),
        tmp_path / "SKILLS" / "decompose-task",
    )
    # Domain skill (nested under SKILLS/domain/)
    write_skill(
        Skill(name="my-custom-thing", description="Project-specific procedure description.", body="# Y\n## Steps\n1. z"),
        tmp_path / "SKILLS" / "domain" / "my-custom-thing",
    )

    skills = list_skills(tmp_path / "SKILLS")
    names = {s.name for s in skills}
    assert names == {"decompose-task", "my-custom-thing"}


def test_domain_skill_passes_validate(tmp_path: Path) -> None:
    skill = Skill(
        name="fetch-quotes",
        description="Fetch quotes from Polygon REST and normalize to OHLCV.",
        version="0.1.0",
        when_to_use="When the user asks for a quote on a ticker.",
        body="# Fetch quotes\n\n## Steps\n1. Auth.\n2. GET endpoint.\n",
    )
    issues = validate_skill(skill)
    assert issues == []
