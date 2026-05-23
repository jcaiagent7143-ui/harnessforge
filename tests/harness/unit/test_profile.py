"""Unit tests for HarnessProfile (template builder + YAML I/O)."""

from __future__ import annotations

from pathlib import Path

from harness.inspect_ import inspect_repo
from harness.profile import HarnessProfile, profile_from_inspection_template


def test_template_builder_picks_python(tmp_repo: Path) -> None:
    report = inspect_repo(tmp_repo)
    profile = profile_from_inspection_template(report)
    assert profile.primary_language == "python"
    assert "fastapi" in profile.frameworks
    assert profile.test_command and "pytest" in profile.test_command
    assert ".env" in profile.forbidden_paths
    assert "rm -rf /" in profile.forbidden_commands
    assert profile.success_criteria  # not empty
    assert profile.conventions  # not empty


def test_template_builder_picks_node(tmp_node_repo: Path) -> None:
    report = inspect_repo(tmp_node_repo)
    profile = profile_from_inspection_template(report)
    assert profile.primary_language == "typescript"
    assert "next.js" in profile.frameworks
    assert profile.project_type in {"web-app", "library", "other"}
    assert ".next/" in profile.forbidden_paths


def test_yaml_roundtrip(tmp_repo: Path) -> None:
    report = inspect_repo(tmp_repo)
    profile = profile_from_inspection_template(report)
    yaml_text = profile.to_yaml()
    reparsed = HarnessProfile.from_yaml(yaml_text)
    assert reparsed.name == profile.name
    assert reparsed.primary_language == profile.primary_language
    assert reparsed.frameworks == profile.frameworks


def test_save_and_load(tmp_repo: Path, tmp_path: Path) -> None:
    report = inspect_repo(tmp_repo)
    profile = profile_from_inspection_template(report)
    out = tmp_path / "profile.yaml"
    profile.save(out)
    loaded = HarnessProfile.load(out)
    assert loaded.name == profile.name
