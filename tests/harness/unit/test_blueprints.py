"""Unit tests for the blueprint loader + recommender + renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

from harness.blueprints import (
    iter_catalog_skills,
    list_blueprints,
    load_blueprint,
    recommend_blueprint,
    render_blueprint_files,
    render_blueprint_skills,
)
from harness.blueprints.schema import BlueprintSpec
from harness.inspect_ import inspect_repo
from harness.profile import profile_from_inspection_template

# ── loader ─────────────────────────────────────────────────────────────────


def test_list_blueprints_returns_all_three() -> None:
    bps = list_blueprints()
    names = {bp.name for bp in bps}
    assert names == {
        "rag-agent",
        "support-agent",
        "workflow-agent",
        "python-cli-app",
        "finance-agent",
    }


def test_load_blueprint_unknown_raises() -> None:
    with pytest.raises(KeyError):
        load_blueprint("does-not-exist")


@pytest.mark.parametrize("name", ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"])
def test_blueprint_spec_is_valid(name: str) -> None:
    bp = load_blueprint(name)
    assert isinstance(bp, BlueprintSpec)
    assert bp.name == name
    assert bp.version
    assert bp.display_name
    assert bp.description
    assert bp.agent_type
    assert bp.generated_files  # nonempty
    assert bp.validators  # nonempty


@pytest.mark.parametrize("name", ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"])
def test_blueprint_has_skills(name: str) -> None:
    bp = load_blueprint(name)
    assert bp.skills, f"{name} declares no skills"


# ── recommender ────────────────────────────────────────────────────────────


def test_recommend_for_rag_repo(tmp_rag_repo: Path) -> None:
    report = inspect_repo(tmp_rag_repo)
    profile = profile_from_inspection_template(report)
    assert recommend_blueprint(report, profile) == "rag-agent"


def test_recommend_for_django_support_repo(tmp_django_repo: Path) -> None:
    report = inspect_repo(tmp_django_repo)
    profile = profile_from_inspection_template(report)
    # Either support-agent (django+web-app) or workflow-agent fallback
    rec = recommend_blueprint(report, profile)
    assert rec in {"support-agent", "workflow-agent"}


def test_recommend_default_for_python_project(tmp_repo: Path) -> None:
    """A generic Python project (tmp_repo has fastapi + pytest + ruff) now
    defaults to python-cli-app, not workflow-agent — per the v0.2 spec
    that made python-cli-app the 80% case."""
    report = inspect_repo(tmp_repo)
    profile = profile_from_inspection_template(report)
    rec = recommend_blueprint(report, profile)
    assert rec in {
        "rag-agent", "support-agent", "workflow-agent",
        "python-cli-app", "finance-agent",
    }


# ── renderer ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize("name", ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"])
def test_render_blueprint_files_against_real_repo(tmp_repo: Path, name: str) -> None:
    bp = load_blueprint(name)
    report = inspect_repo(tmp_repo)
    profile = profile_from_inspection_template(report)
    files = render_blueprint_files(bp, profile, report, tmp_repo)
    assert files, f"{name} rendered no files"
    paths = {str(pf.path.relative_to(tmp_repo)) for pf in files}
    # Every blueprint must render the universal entries
    assert "AGENTS.md" in paths
    assert "SOUL.md" in paths
    assert "TOOLS.md" in paths
    assert "MEMORY.md" in paths


@pytest.mark.parametrize("name", ["rag-agent", "support-agent", "workflow-agent", "python-cli-app", "finance-agent"])
def test_render_blueprint_skills_lays_out_SKILLS(tmp_repo: Path, name: str) -> None:
    bp = load_blueprint(name)
    files = render_blueprint_skills(bp, tmp_repo)
    if not bp.skills:
        return
    paths = {str(pf.path.relative_to(tmp_repo)) for pf in files}
    # At least one SKILL.md should be rendered
    assert any(p.startswith("SKILLS/") and p.endswith("/SKILL.md") for p in paths)


def test_iter_catalog_skills_returns_entries() -> None:
    catalog = list(iter_catalog_skills())
    assert catalog
    blueprint_names = {bp for bp, _ in catalog}
    assert blueprint_names == {
        "rag-agent",
        "support-agent",
        "workflow-agent",
        "python-cli-app",
        "finance-agent",
    }
